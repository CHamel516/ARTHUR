"""
ARTHUR Schedule Management Feature
Handles class schedules and assignments
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..core.memory import Memory


class ScheduleManager:
    """Manages class schedule and assignments"""

    DAY_NAMES = {
        'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday',
        'R': 'Thursday', 'F': 'Friday', 'S': 'Saturday', 'U': 'Sunday'
    }

    DAY_ABBREVS = {
        'monday': 'M', 'tuesday': 'T', 'wednesday': 'W',
        'thursday': 'R', 'friday': 'F', 'saturday': 'S', 'sunday': 'U',
        'mon': 'M', 'tue': 'T', 'wed': 'W', 'thu': 'R', 'fri': 'F',
        'sat': 'S', 'sun': 'U'
    }

    def __init__(self, memory: Memory):
        self.memory = memory

    def _parse_days(self, days_input: str) -> str:
        """Parse day input into standard format (MWF, TR, etc.)"""
        days_input = days_input.lower().strip()

        if all(c in 'mtwrfsu' for c in days_input.replace(' ', '')):
            return days_input.upper().replace(' ', '')

        result = []
        for word in days_input.replace(',', ' ').split():
            if word in self.DAY_ABBREVS:
                result.append(self.DAY_ABBREVS[word])
        return ''.join(result) if result else days_input.upper()

    def _parse_time(self, time_str: str) -> str:
        """Parse time input into 24-hour format"""
        time_str = time_str.lower().strip()

        formats = ['%I:%M%p', '%I:%M %p', '%I%p', '%I %p', '%H:%M']

        for fmt in formats:
            try:
                parsed = datetime.strptime(time_str, fmt)
                return parsed.strftime('%H:%M')
            except ValueError:
                continue

        return time_str

    def add_class(self, title: str, days: str, start_time: str,
                  end_time: str = "", location: str = "") -> str:
        """
        Add a class to the schedule

        Args:
            title: Class name (e.g., "Chemistry 101")
            days: Days of the week (e.g., "MWF" or "Monday Wednesday Friday")
            start_time: Start time (e.g., "10:00 AM" or "10:00")
            end_time: End time (optional)
            location: Room/building (optional)

        Returns:
            Confirmation message
        """
        parsed_days = self._parse_days(days)
        parsed_start = self._parse_time(start_time)
        parsed_end = self._parse_time(end_time) if end_time else ""

        self.memory.add_class(title, parsed_days, parsed_start, parsed_end, location)

        day_names = [self.DAY_NAMES.get(d, d) for d in parsed_days]
        days_str = ', '.join(day_names)

        response = f"Added {title} on {days_str} at {parsed_start}"
        if location:
            response += f" in {location}"
        return response + "."

    def view_schedule(self, day: Optional[str] = None) -> str:
        """
        View class schedule

        Args:
            day: Optional specific day to view

        Returns:
            Formatted schedule string
        """
        if day:
            parsed_day = self._parse_days(day)
            if len(parsed_day) == 1:
                schedule = self.memory.get_schedule(parsed_day)
                day_name = self.DAY_NAMES.get(parsed_day, day)
                if not schedule:
                    return f"You have no classes scheduled for {day_name}."
                header = f"Classes on {day_name}:"
            else:
                schedule = self.memory.get_schedule()
                header = "Your class schedule:"
        else:
            schedule = self.memory.get_schedule()
            header = "Your class schedule:"

        if not schedule:
            return "You haven't added any classes to your schedule yet."

        lines = [header]
        for cls in schedule:
            day_names = [self.DAY_NAMES.get(d, d) for d in cls['days']]
            days_str = '/'.join(day_names)
            time_str = cls['start_time']
            if cls['end_time']:
                time_str += f" - {cls['end_time']}"

            line = f"  {cls['title']}: {days_str} at {time_str}"
            if cls['location']:
                line += f" ({cls['location']})"
            lines.append(line)

        return "\n".join(lines)

    def get_next_class(self) -> str:
        """Get information about the next upcoming class"""
        next_class = self.memory.get_next_class()

        if not next_class:
            return "I don't see any upcoming classes in your schedule."

        response = f"Your next class is {next_class['title']} at {next_class['start_time']}"
        if next_class['location']:
            response += f" in {next_class['location']}"
        return response + "."

    def add_assignment(self, title: str, due_date: str, course: str = "",
                       description: str = "", priority: int = 2) -> str:
        """
        Add an assignment

        Args:
            title: Assignment name
            due_date: Due date (various formats accepted)
            course: Course name (optional)
            description: Details (optional)
            priority: 1-3 (optional)

        Returns:
            Confirmation message
        """
        parsed_date = self._parse_date(due_date)
        self.memory.add_assignment(title, parsed_date, course, description, priority)

        response = f"Assignment added: '{title}' due {parsed_date}"
        if course:
            response += f" for {course}"
        return response + "."

    def _parse_date(self, date_str: str) -> str:
        """Parse date input into YYYY-MM-DD format"""
        date_str = date_str.lower().strip()
        today = datetime.now()

        if date_str == 'today':
            return today.strftime('%Y-%m-%d')
        elif date_str == 'tomorrow':
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')

        day_offsets = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        if date_str in day_offsets:
            target_day = day_offsets[date_str]
            current_day = today.weekday()
            days_ahead = target_day - current_day
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        formats = ['%Y-%m-%d', '%m/%d/%Y', '%m/%d', '%B %d', '%b %d']
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=today.year)
                    if parsed < today:
                        parsed = parsed.replace(year=today.year + 1)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return date_str

    def view_assignments(self, days_ahead: int = None) -> str:
        """
        View assignments

        Args:
            days_ahead: Optional filter for assignments due within N days

        Returns:
            Formatted assignment list
        """
        if days_ahead:
            assignments = self.memory.get_upcoming_assignments(days_ahead)
            header = f"Assignments due in the next {days_ahead} days:"
        else:
            assignments = self.memory.get_assignments()
            header = "Your assignments:"

        if not assignments:
            if days_ahead:
                return f"No assignments due in the next {days_ahead} days."
            return "You have no pending assignments. Well prepared, sir."

        lines = [header]
        for a in assignments:
            line = f"  - {a['title']} (due {a['due_date']})"
            if a['course']:
                line += f" [{a['course']}]"
            lines.append(line)

        return "\n".join(lines)

    def complete_assignment(self, identifier: str) -> str:
        """Mark an assignment as complete"""
        assignments = self.memory.get_assignments()

        if identifier.isdigit():
            idx = int(identifier) - 1
            if 0 <= idx < len(assignments):
                assignment = assignments[idx]
                self.memory.complete_assignment(assignment['id'])
                return f"Assignment '{assignment['title']}' marked as complete. Well done."
            return "I couldn't find an assignment with that number."

        for assignment in assignments:
            if identifier.lower() in assignment['title'].lower():
                self.memory.complete_assignment(assignment['id'])
                return f"Assignment '{assignment['title']}' marked as complete."

        return f"I couldn't find an assignment matching '{identifier}'."

    def get_week_summary(self) -> str:
        """Get a summary of the upcoming week"""
        assignments = self.memory.get_upcoming_assignments(7)
        schedule = self.memory.get_schedule()

        parts = []

        if assignments:
            parts.append(f"You have {len(assignments)} assignment{'s' if len(assignments) != 1 else ''} due this week.")
        else:
            parts.append("No assignments due this week.")

        if schedule:
            parts.append(f"You have {len(schedule)} class{'es' if len(schedule) != 1 else ''} scheduled.")

        return " ".join(parts)
