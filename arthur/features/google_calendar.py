"""
ARTHUR Google Calendar Integration
Connects to Google Calendar for events and scheduling
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleCalendarIntegration:
    """Handles Google Calendar API integration"""

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Calendar integration

        Args:
            credentials_path: Path to credentials.json from Google Cloud Console
        """
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)

        self.credentials_path = credentials_path or str(self.data_dir / "google_credentials.json")
        self.token_path = str(self.data_dir / "google_token.pickle")

        self.service = None
        self.is_authenticated = False

        self._try_authenticate()

    def _try_authenticate(self):
        """Try to authenticate with saved credentials"""
        creds = None

        # Load saved token if exists
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except:
                pass

        # Check if credentials are valid
        if creds and creds.valid:
            self._build_service(creds)
        elif creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
                self._build_service(creds)
            except:
                pass

    def _build_service(self, creds):
        """Build the calendar service"""
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            self.is_authenticated = True
        except Exception as e:
            print(f"Error building calendar service: {e}")
            self.is_authenticated = False

    def _save_token(self, creds):
        """Save credentials token"""
        with open(self.token_path, 'wb') as token:
            pickle.dump(creds, token)

    def authenticate(self) -> bool:
        """
        Run OAuth flow to authenticate with Google

        Returns:
            True if authentication successful
        """
        if not os.path.exists(self.credentials_path):
            print(f"Credentials file not found: {self.credentials_path}")
            print("Download credentials.json from Google Cloud Console")
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            creds = flow.run_local_server(port=0)
            self._save_token(creds)
            self._build_service(creds)
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def is_configured(self) -> bool:
        """Check if calendar is properly configured"""
        return self.is_authenticated and self.service is not None

    def get_upcoming_events(self, days_ahead: int = 7, max_results: int = 20) -> List[Dict]:
        """
        Get upcoming calendar events

        Args:
            days_ahead: Number of days to look ahead
            max_results: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        if not self.is_configured():
            return []

        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = []
            for event in events_result.get('items', []):
                parsed = self._parse_event(event)
                if parsed:
                    events.append(parsed)

            return events

        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

    def _parse_event(self, event: Dict) -> Optional[Dict]:
        """Parse a Google Calendar event"""
        try:
            start = event.get('start', {})
            end = event.get('end', {})

            # Get start time (could be date or dateTime)
            start_str = start.get('dateTime', start.get('date', ''))
            end_str = end.get('dateTime', end.get('date', ''))

            # Check if all-day event
            is_all_day = 'date' in start and 'dateTime' not in start

            return {
                'title': event.get('summary', 'Untitled'),
                'start': start_str,
                'end': end_str,
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'is_all_day': is_all_day,
                'id': event.get('id', '')
            }
        except:
            return None

    def get_today_events(self) -> str:
        """Get formatted string of today's events"""
        if not self.is_configured():
            return "Google Calendar not connected. Run 'connect google calendar' to set up."

        events = self.get_upcoming_events(days_ahead=1)

        # Filter to just today
        today = datetime.now().date()
        today_events = []
        for event in events:
            try:
                event_date = event['start'].split('T')[0]
                if datetime.fromisoformat(event_date).date() == today:
                    today_events.append(event)
            except:
                pass

        if not today_events:
            return "No events scheduled for today."

        lines = ["Today's calendar:"]
        for event in today_events:
            time_str = ""
            if not event['is_all_day']:
                try:
                    dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    time_str = dt.strftime('%I:%M %p')
                except:
                    pass

            if time_str:
                lines.append(f"  {time_str} - {event['title']}")
            else:
                lines.append(f"  All day - {event['title']}")

            if event['location']:
                lines.append(f"    Location: {event['location']}")

        return "\n".join(lines)

    def get_upcoming_formatted(self, days: int = 7) -> str:
        """Get formatted string of upcoming events"""
        if not self.is_configured():
            return "Google Calendar not connected. Run 'connect google calendar' to set up."

        events = self.get_upcoming_events(days_ahead=days)

        if not events:
            return f"No events in the next {days} days."

        lines = [f"Upcoming events (next {days} days):"]

        current_date = None
        for event in events:
            try:
                event_date = event['start'].split('T')[0]
                dt = datetime.fromisoformat(event_date)

                if event_date != current_date:
                    current_date = event_date
                    lines.append(f"\n  {dt.strftime('%A, %B %d')}:")

                time_str = ""
                if not event['is_all_day']:
                    try:
                        start_dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                        time_str = f" at {start_dt.strftime('%I:%M %p')}"
                    except:
                        pass

                lines.append(f"    {event['title']}{time_str}")
            except:
                lines.append(f"    {event['title']}")

        return "\n".join(lines)

    def get_next_event(self) -> str:
        """Get the next upcoming event"""
        if not self.is_configured():
            return "Calendar not connected."

        events = self.get_upcoming_events(days_ahead=7, max_results=1)

        if not events:
            return "No upcoming events."

        event = events[0]
        try:
            if event['is_all_day']:
                dt = datetime.fromisoformat(event['start'])
                time_str = dt.strftime('%A, %B %d')
                return f"Next event: {event['title']} on {time_str} (all day)"
            else:
                dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                time_str = dt.strftime('%I:%M %p on %A')
                result = f"Next event: {event['title']} at {time_str}"
                if event['location']:
                    result += f" at {event['location']}"
                return result
        except:
            return f"Next event: {event['title']}"

    def get_events_summary(self) -> str:
        """Get a quick summary for daily briefing"""
        if not self.is_configured():
            return "Calendar not connected"

        today_events = self.get_upcoming_events(days_ahead=1)
        today = datetime.now().date()

        today_count = 0
        for event in today_events:
            try:
                event_date = event['start'].split('T')[0]
                if datetime.fromisoformat(event_date).date() == today:
                    today_count += 1
            except:
                pass

        if today_count == 0:
            return "No events today"
        elif today_count == 1:
            return "1 event today"
        else:
            return f"{today_count} events today"
