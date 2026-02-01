"""
ARTHUR Reminder Feature
Handles time-based reminders and notifications
"""

from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
import threading
import time
from ..core.memory import Memory


class ReminderManager:
    """Manages reminders and notifications"""

    def __init__(self, memory: Memory, notification_callback: Optional[Callable] = None):
        """
        Initialize reminder manager

        Args:
            memory: Memory instance for storage
            notification_callback: Function to call when reminder is due
                                   Signature: callback(message: str)
        """
        self.memory = memory
        self.notification_callback = notification_callback
        self.running = False
        self.checker_thread: Optional[threading.Thread] = None

    def add_reminder(self, message: str, time_str: str) -> str:
        """
        Add a new reminder

        Args:
            message: Reminder message
            time_str: When to remind (e.g., "3pm", "in 30 minutes", "tomorrow at 9am")

        Returns:
            Confirmation message
        """
        remind_at = self._parse_reminder_time(time_str)

        if remind_at is None:
            return f"I couldn't understand the time '{time_str}'. Try something like '3pm' or 'in 30 minutes'."

        if remind_at <= datetime.now():
            return "That time has already passed. Please specify a future time."

        self.memory.add_reminder(message, remind_at)

        time_display = remind_at.strftime('%I:%M %p on %A, %B %d')
        return f"Reminder set: '{message}' at {time_display}."

    def _parse_reminder_time(self, time_str: str) -> Optional[datetime]:
        """Parse time string into datetime"""
        time_str = time_str.lower().strip()
        now = datetime.now()

        if time_str.startswith('in '):
            relative = time_str[3:].strip()

            if 'minute' in relative:
                try:
                    minutes = int(relative.split()[0])
                    return now + timedelta(minutes=minutes)
                except:
                    pass

            if 'hour' in relative:
                try:
                    hours = int(relative.split()[0])
                    return now + timedelta(hours=hours)
                except:
                    pass

        if 'at' in time_str:
            parts = time_str.split('at')
            day_part = parts[0].strip()
            time_part = parts[1].strip() if len(parts) > 1 else ""

            target_date = now.date()

            if 'tomorrow' in day_part:
                target_date = (now + timedelta(days=1)).date()

            if time_part:
                target_time = self._parse_time_only(time_part)
                if target_time:
                    return datetime.combine(target_date, target_time)

        time_only = self._parse_time_only(time_str)
        if time_only:
            result = datetime.combine(now.date(), time_only)
            if result <= now:
                result += timedelta(days=1)
            return result

        return None

    def _parse_time_only(self, time_str: str) -> Optional[datetime]:
        """Parse just a time (e.g., '3pm', '15:30')"""
        time_str = time_str.strip().lower()

        formats = ['%I:%M%p', '%I:%M %p', '%I%p', '%I %p', '%H:%M']

        for fmt in formats:
            try:
                parsed = datetime.strptime(time_str, fmt)
                return parsed.time()
            except ValueError:
                continue

        return None

    def view_reminders(self) -> str:
        """View all pending reminders"""
        reminders = self.memory.get_pending_reminders()

        if not reminders:
            return "You have no pending reminders."

        lines = ["Your reminders:"]
        for i, reminder in enumerate(reminders, 1):
            remind_at = reminder['remind_at']
            if isinstance(remind_at, str):
                remind_at = datetime.fromisoformat(remind_at)

            time_display = remind_at.strftime('%I:%M %p, %b %d')
            lines.append(f"  {i}. {reminder['message']} - {time_display}")

        return "\n".join(lines)

    def check_reminders(self) -> List[str]:
        """
        Check for due reminders

        Returns:
            List of reminder messages that are due
        """
        due_reminders = self.memory.get_due_reminders()
        messages = []

        for reminder in due_reminders:
            messages.append(reminder['message'])
            self.memory.complete_reminder(reminder['id'])

        return messages

    def start_checker(self, interval_seconds: int = 30):
        """
        Start background thread to check for due reminders

        Args:
            interval_seconds: How often to check (default 30 seconds)
        """
        if self.running:
            return

        self.running = True
        self.checker_thread = threading.Thread(
            target=self._checker_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.checker_thread.start()

    def _checker_loop(self, interval: int):
        """Background loop to check reminders"""
        while self.running:
            due_messages = self.check_reminders()

            for message in due_messages:
                if self.notification_callback:
                    self.notification_callback(f"Reminder: {message}")
                else:
                    print(f"\n[REMINDER] {message}\n")

            time.sleep(interval)

    def stop_checker(self):
        """Stop the background reminder checker"""
        self.running = False
        if self.checker_thread:
            self.checker_thread.join(timeout=2)

    def cancel_reminder(self, identifier: str) -> str:
        """
        Cancel a reminder by number

        Args:
            identifier: Reminder number

        Returns:
            Confirmation message
        """
        reminders = self.memory.get_pending_reminders()

        if identifier.isdigit():
            idx = int(identifier) - 1
            if 0 <= idx < len(reminders):
                reminder = reminders[idx]
                self.memory.complete_reminder(reminder['id'])
                return f"Reminder '{reminder['message']}' cancelled."
            return "I couldn't find a reminder with that number."

        return "Please specify the reminder number to cancel."

    def get_reminder_count(self) -> int:
        """Get count of pending reminders"""
        return len(self.memory.get_pending_reminders())
