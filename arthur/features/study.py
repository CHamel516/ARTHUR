"""
ARTHUR Study Timer Feature
Pomodoro technique and focus session management
"""

from typing import Optional, Callable
from datetime import datetime, timedelta
import threading
import time
from ..core.memory import Memory


class StudyTimer:
    """Manages study/focus sessions using Pomodoro technique"""

    DEFAULT_WORK_DURATION = 25
    DEFAULT_SHORT_BREAK = 5
    DEFAULT_LONG_BREAK = 15
    POMODOROS_UNTIL_LONG_BREAK = 4

    def __init__(self, memory: Memory,
                 on_session_complete: Optional[Callable] = None,
                 on_break_complete: Optional[Callable] = None,
                 on_tick: Optional[Callable] = None):
        """
        Initialize study timer

        Args:
            memory: Memory instance for logging sessions
            on_session_complete: Callback when work session ends
            on_break_complete: Callback when break ends
            on_tick: Callback every minute with remaining time
        """
        self.memory = memory
        self.on_session_complete = on_session_complete
        self.on_break_complete = on_break_complete
        self.on_tick = on_tick

        self.is_active = False
        self.is_break = False
        self.current_subject: Optional[str] = None
        self.session_start: Optional[datetime] = None
        self.session_duration: int = self.DEFAULT_WORK_DURATION
        self.remaining_seconds: int = 0
        self.pomodoro_count: int = 0

        self.timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start_session(self, duration_minutes: int = None, subject: str = "") -> str:
        """
        Start a focus/study session

        Args:
            duration_minutes: Session length (default 25)
            subject: What you're studying (optional)

        Returns:
            Confirmation message
        """
        if self.is_active:
            remaining = self.remaining_seconds // 60
            return f"A session is already in progress with {remaining} minutes remaining."

        duration = duration_minutes or self.DEFAULT_WORK_DURATION
        self.session_duration = duration
        self.current_subject = subject
        self.session_start = datetime.now()
        self.remaining_seconds = duration * 60
        self.is_active = True
        self.is_break = False

        self._stop_event.clear()
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()

        response = f"Starting {duration}-minute focus session."
        if subject:
            response = f"Starting {duration}-minute focus session for {subject}."
        response += " I'll notify you when it's time for a break. Good luck, sir."

        return response

    def _run_timer(self):
        """Background timer thread"""
        last_minute_announced = self.remaining_seconds // 60

        while self.remaining_seconds > 0 and not self._stop_event.is_set():
            time.sleep(1)
            self.remaining_seconds -= 1

            current_minute = self.remaining_seconds // 60
            if current_minute != last_minute_announced and self.on_tick:
                self.on_tick(self.remaining_seconds, self.is_break)
                last_minute_announced = current_minute

        if not self._stop_event.is_set():
            self._complete_session()

    def _complete_session(self):
        """Handle session completion"""
        if self.is_break:
            self.is_active = False
            self.is_break = False
            if self.on_break_complete:
                self.on_break_complete()
        else:
            self.memory.log_study_session(
                subject=self.current_subject or "General",
                duration_minutes=self.session_duration,
                started_at=self.session_start,
                ended_at=datetime.now(),
                completed=True
            )

            self.pomodoro_count += 1

            if self.on_session_complete:
                is_long_break = (self.pomodoro_count % self.POMODOROS_UNTIL_LONG_BREAK == 0)
                break_duration = self.DEFAULT_LONG_BREAK if is_long_break else self.DEFAULT_SHORT_BREAK
                self.on_session_complete(self.pomodoro_count, break_duration)

            self.is_active = False

    def start_break(self, duration_minutes: int = None) -> str:
        """
        Start a break

        Args:
            duration_minutes: Break length (default based on pomodoro count)

        Returns:
            Confirmation message
        """
        if self.is_active and not self.is_break:
            return "You're in the middle of a focus session. Use 'stop session' first if you need a break now."

        is_long = (self.pomodoro_count % self.POMODOROS_UNTIL_LONG_BREAK == 0) and self.pomodoro_count > 0
        default_break = self.DEFAULT_LONG_BREAK if is_long else self.DEFAULT_SHORT_BREAK
        duration = duration_minutes or default_break

        self.remaining_seconds = duration * 60
        self.is_active = True
        self.is_break = True

        self._stop_event.clear()
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()

        break_type = "long" if is_long else "short"
        return f"Starting {duration}-minute {break_type} break. You've earned it."

    def stop_session(self) -> str:
        """Stop the current session or break"""
        if not self.is_active:
            return "No session is currently active."

        self._stop_event.set()
        if self.timer_thread:
            self.timer_thread.join(timeout=2)

        if self.is_break:
            self.is_active = False
            self.is_break = False
            return "Break ended early. Ready when you are."

        elapsed_minutes = (self.session_duration * 60 - self.remaining_seconds) // 60

        if elapsed_minutes >= 5:
            self.memory.log_study_session(
                subject=self.current_subject or "General",
                duration_minutes=elapsed_minutes,
                started_at=self.session_start,
                ended_at=datetime.now(),
                completed=False
            )

        self.is_active = False
        return f"Session stopped after {elapsed_minutes} minutes."

    def get_status(self) -> str:
        """Get current timer status"""
        if not self.is_active:
            return "No active session. Say 'start focus session' to begin."

        remaining_min = self.remaining_seconds // 60
        remaining_sec = self.remaining_seconds % 60

        if self.is_break:
            return f"Break in progress: {remaining_min}:{remaining_sec:02d} remaining."

        status = f"Focus session in progress: {remaining_min}:{remaining_sec:02d} remaining."
        if self.current_subject:
            status += f" Subject: {self.current_subject}"
        return status

    def get_study_stats(self, days: int = 7) -> str:
        """
        Get study statistics

        Args:
            days: Number of days to look back

        Returns:
            Formatted statistics string
        """
        stats = self.memory.get_study_stats(days)

        if stats['session_count'] == 0:
            return f"No study sessions logged in the past {days} days."

        total_hours = stats['total_minutes'] // 60
        total_remaining_min = stats['total_minutes'] % 60
        avg_duration = int(stats['avg_duration'])

        lines = [
            f"Study statistics for the past {days} days:",
            f"  Total study time: {total_hours}h {total_remaining_min}m",
            f"  Sessions completed: {stats['session_count']}",
            f"  Average session: {avg_duration} minutes",
            f"  Pomodoros today: {self.pomodoro_count}"
        ]

        return "\n".join(lines)

    def reset_pomodoro_count(self):
        """Reset the daily pomodoro counter"""
        self.pomodoro_count = 0
