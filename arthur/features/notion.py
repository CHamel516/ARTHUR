"""
ARTHUR Notion Integration
Connects to Notion calendars and databases
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from notion_client import Client


class NotionIntegration:
    """Handles Notion API integration for calendars and tasks"""

    def __init__(self, api_key: Optional[str] = None, calendar_db_id: Optional[str] = None):
        """
        Initialize Notion integration

        Args:
            api_key: Notion Integration API key
            calendar_db_id: Database ID for calendar/events
        """
        self.api_key = api_key
        self.calendar_db_id = calendar_db_id
        self.client: Optional[Client] = None

        if api_key:
            self._connect()

    def _connect(self):
        """Connect to Notion API"""
        try:
            self.client = Client(auth=self.api_key)
            self.client.users.me()
            print("Notion connection established")
        except Exception as e:
            print(f"Notion connection failed: {e}")
            self.client = None

    def configure(self, api_key: str, calendar_db_id: str = None):
        """Configure Notion credentials"""
        self.api_key = api_key
        self.calendar_db_id = calendar_db_id
        self._connect()

    def is_configured(self) -> bool:
        """Check if Notion is properly configured"""
        return self.client is not None

    def get_calendar_events(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get upcoming calendar events from Notion

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of event dictionaries
        """
        if not self.client or not self.calendar_db_id:
            return []

        try:
            today = datetime.now().date()
            end_date = today + timedelta(days=days_ahead)

            response = self.client.databases.query(
                database_id=self.calendar_db_id,
                filter={
                    "and": [
                        {
                            "property": "Date",
                            "date": {
                                "on_or_after": today.isoformat()
                            }
                        },
                        {
                            "property": "Date",
                            "date": {
                                "on_or_before": end_date.isoformat()
                            }
                        }
                    ]
                },
                sorts=[
                    {
                        "property": "Date",
                        "direction": "ascending"
                    }
                ]
            )

            events = []
            for page in response.get('results', []):
                event = self._parse_event(page)
                if event:
                    events.append(event)

            return events

        except Exception as e:
            print(f"Error fetching Notion events: {e}")
            return []

    def _parse_event(self, page: Dict) -> Optional[Dict]:
        """Parse a Notion page into an event dictionary"""
        try:
            props = page.get('properties', {})

            title = ""
            title_prop = props.get('Name') or props.get('Title') or props.get('title')
            if title_prop and title_prop.get('title'):
                title = title_prop['title'][0]['plain_text'] if title_prop['title'] else ""

            date_str = ""
            date_prop = props.get('Date') or props.get('date')
            if date_prop and date_prop.get('date'):
                date_info = date_prop['date']
                date_str = date_info.get('start', '')

            status = ""
            status_prop = props.get('Status') or props.get('status')
            if status_prop:
                if status_prop.get('select'):
                    status = status_prop['select'].get('name', '')
                elif status_prop.get('status'):
                    status = status_prop['status'].get('name', '')

            return {
                'title': title,
                'date': date_str,
                'status': status,
                'id': page.get('id', '')
            }

        except Exception as e:
            print(f"Error parsing event: {e}")
            return None

    def get_today_events(self) -> str:
        """Get formatted string of today's events"""
        events = self.get_calendar_events(days_ahead=1)

        if not events:
            if not self.is_configured():
                return "Notion not configured. Run config to set up."
            return "No events scheduled for today in Notion."

        lines = ["Today's Notion events:"]
        for event in events:
            time_str = ""
            if 'T' in event['date']:
                try:
                    dt = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
                    time_str = f" at {dt.strftime('%I:%M %p')}"
                except:
                    pass

            lines.append(f"  - {event['title']}{time_str}")

        return "\n".join(lines)

    def get_upcoming_events(self, days: int = 7) -> str:
        """Get formatted string of upcoming events"""
        events = self.get_calendar_events(days_ahead=days)

        if not events:
            if not self.is_configured():
                return "Notion not configured. Set your API key and calendar database ID in config."
            return f"No events in the next {days} days."

        lines = [f"Upcoming events (next {days} days):"]

        current_date = None
        for event in events:
            event_date = event['date'].split('T')[0] if 'T' in event['date'] else event['date']

            if event_date != current_date:
                current_date = event_date
                try:
                    dt = datetime.fromisoformat(event_date)
                    lines.append(f"\n  {dt.strftime('%A, %B %d')}:")
                except:
                    lines.append(f"\n  {event_date}:")

            time_str = ""
            if 'T' in event['date']:
                try:
                    dt = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
                    time_str = f" ({dt.strftime('%I:%M %p')})"
                except:
                    pass

            status = f" [{event['status']}]" if event['status'] else ""
            lines.append(f"    - {event['title']}{time_str}{status}")

        return "\n".join(lines)

    def search_events(self, query: str) -> str:
        """Search for events by name"""
        if not self.client or not self.calendar_db_id:
            return "Notion not configured."

        try:
            response = self.client.databases.query(
                database_id=self.calendar_db_id,
                filter={
                    "property": "Name",
                    "title": {
                        "contains": query
                    }
                }
            )

            events = [self._parse_event(p) for p in response.get('results', [])]
            events = [e for e in events if e]

            if not events:
                return f"No events found matching '{query}'."

            lines = [f"Events matching '{query}':"]
            for event in events[:10]:
                lines.append(f"  - {event['title']} ({event['date']})")

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching Notion: {e}"
