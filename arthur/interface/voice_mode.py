"""
ARTHUR Voice Mode Interface
JARVIS-style pure voice interaction
"""

import time
from typing import Optional
from ..core.brain import Brain
from ..core.ears import Ears
from ..core.voice import Voice, VoiceMode
from ..core.memory import Memory
from ..features.tasks import TaskManager
from ..features.schedule import ScheduleManager
from ..features.reminders import ReminderManager
from ..features.study import StudyTimer
from ..features.weather import WeatherService
from ..features.planner import PlanningAssistant


class VoiceInterface:
    """Pure voice interaction mode for ARTHUR"""

    def __init__(self, config: dict = None):
        """
        Initialize voice interface

        Args:
            config: Optional configuration dict
        """
        config = config or {}

        print("Initializing A.R.T.H.U.R. systems...")

        self.memory = Memory()
        print("  Memory systems online...")

        self.brain = Brain(model=config.get('model', 'llama3.2:latest'))
        print("  Neural networks initialized...")

        self.ears = Ears()
        print("  Audio receptors calibrated...")

        voice_mode = VoiceMode.HIGH_QUALITY if config.get('high_quality_voice') else VoiceMode.OFFLINE
        self.voice = Voice(mode=voice_mode)
        print("  Voice synthesis ready...")

        self.tasks = TaskManager(self.memory)
        self.schedule = ScheduleManager(self.memory)
        self.reminders = ReminderManager(self.memory, self._speak_reminder)
        self.study = StudyTimer(
            self.memory,
            on_session_complete=self._on_study_complete,
            on_break_complete=self._on_break_complete
        )
        self.weather = WeatherService(
            api_key=config.get('weather_api_key'),
            default_city=config.get('default_city', '')
        )
        self.planner = PlanningAssistant(self.memory, self.brain)
        print("  All subsystems operational.")

        self.is_active = False
        self.conversation_active = False
        self.last_interaction = 0
        self.conversation_timeout = 30

    def _speak_reminder(self, message: str):
        """Callback for reminder notifications"""
        self.voice.speak(message)

    def _on_study_complete(self, pomodoro_count: int, break_duration: int):
        """Callback when study session completes"""
        message = f"Excellent work, sir. You've completed {pomodoro_count} pomodoro"
        if pomodoro_count > 1:
            message += "s"
        message += f" today. Time for a {break_duration}-minute break."
        self.voice.speak(message)

    def _on_break_complete(self):
        """Callback when break completes"""
        self.voice.speak("Break time is over, sir. Ready to resume when you are.")

    def start(self):
        """Start the voice interface"""
        self.is_active = True
        self.reminders.start_checker()

        print("\n" + "=" * 50)
        print("A.R.T.H.U.R. Voice Mode Active")
        print("Say 'Arthur' to begin a conversation")
        print("Press Ctrl+C to exit")
        print("=" * 50 + "\n")

        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.stop()

    def _main_loop(self):
        """Main listening loop"""
        while self.is_active:
            if self.conversation_active:
                if time.time() - self.last_interaction > self.conversation_timeout:
                    self.conversation_active = False
                    print("\n[Conversation timed out - listening for wake word]")
                    continue

                text = self.ears.listen_once()
                if text:
                    self.last_interaction = time.time()
                    self._handle_input(text)
            else:
                result = self.ears.listen_with_wake_word()
                if result is not None:
                    self.conversation_active = True
                    self.last_interaction = time.time()

                    if result:
                        self._handle_input(result)
                    else:
                        greeting = self.brain.get_greeting()
                        print(f"\nARTHUR: {greeting}")
                        self.voice.speak(greeting)

    def _handle_input(self, user_input: str):
        """
        Process user input and generate response

        Args:
            user_input: What the user said
        """
        user_input = user_input.strip()
        if not user_input:
            return

        print(f"\nYou: {user_input}")

        self.memory.save_conversation("user", user_input)

        lower_input = user_input.lower()

        if any(word in lower_input for word in ['goodbye', 'bye', 'see you', 'good night']):
            response = "Goodbye, sir. Have a wonderful day."
            self.conversation_active = False
        elif any(word in lower_input for word in ['stop', 'cancel', 'quiet', 'shut up']):
            self.voice.stop()
            response = "Of course, sir."
        else:
            response = self._process_command(user_input, lower_input)

        print(f"ARTHUR: {response}")
        self.memory.save_conversation("assistant", response)
        self.voice.speak(response)

    def _process_command(self, user_input: str, lower_input: str) -> str:
        """
        Route command to appropriate handler

        Args:
            user_input: Original input
            lower_input: Lowercase version

        Returns:
            Response string
        """
        intent = self.brain.analyze_intent(user_input)
        intent_type = intent.get('intent', 'chat')
        entities = intent.get('entities', {})

        if intent_type == 'task_add':
            task_name = entities.get('task_name') or self._extract_after(lower_input, ['add task', 'new task', 'create task', 'add a task'])
            if task_name:
                return self.tasks.add_task(task_name)

        elif intent_type == 'task_view':
            return self.tasks.view_tasks()

        elif intent_type == 'task_remove':
            task_id = entities.get('task_name') or self._extract_after(lower_input, ['remove task', 'delete task', 'complete task', 'finish task'])
            if task_id:
                if 'complete' in lower_input or 'finish' in lower_input or 'done' in lower_input:
                    return self.tasks.complete_task(task_id)
                return self.tasks.remove_task(task_id)

        elif intent_type == 'schedule_view':
            day = entities.get('day')
            if 'next class' in lower_input:
                return self.schedule.get_next_class()
            return self.schedule.view_schedule(day)

        elif intent_type == 'schedule_add':
            return "To add a class, please specify the name, days, and time. For example: 'Add Chemistry on Monday Wednesday Friday at 10am'"

        elif intent_type == 'assignment_add':
            title = entities.get('task_name', '')
            due_date = entities.get('date', '')
            if title and due_date:
                return self.schedule.add_assignment(title, due_date)

        elif intent_type == 'assignment_view':
            if 'week' in lower_input:
                return self.schedule.view_assignments(7)
            return self.schedule.view_assignments()

        elif intent_type == 'reminder_set':
            parts = self._parse_reminder(lower_input)
            if parts:
                return self.reminders.add_reminder(parts['message'], parts['time'])

        elif intent_type == 'reminder_view':
            return self.reminders.view_reminders()

        elif intent_type == 'study_start':
            duration = entities.get('duration')
            subject = entities.get('subject', '')
            if duration:
                try:
                    duration = int(duration)
                except:
                    duration = None
            return self.study.start_session(duration, subject)

        elif intent_type == 'study_stop':
            return self.study.stop_session()

        elif intent_type == 'weather':
            city = entities.get('location') or self._extract_after(lower_input, ['weather in', 'weather for'])
            if 'umbrella' in lower_input:
                return self.weather.should_bring_umbrella(city)
            return self.weather.get_weather(city)

        elif intent_type == 'planning':
            if 'briefing' in lower_input or 'today' in lower_input:
                return self.planner.get_daily_briefing()
            elif 'prioritize' in lower_input:
                return self.planner.prioritize_tasks()
            elif 'review' in lower_input:
                return self.planner.weekly_review()

        if 'study stats' in lower_input or 'study statistics' in lower_input:
            return self.study.get_study_stats()

        if 'break' in lower_input and 'start' in lower_input:
            return self.study.start_break()

        if 'status' in lower_input or 'timer' in lower_input:
            return self.study.get_status()

        context = self.memory.get_context_summary()
        return self.brain.think(user_input, context)

    def _extract_after(self, text: str, triggers: list) -> str:
        """Extract text after trigger phrases"""
        for trigger in triggers:
            if trigger in text:
                return text.split(trigger, 1)[1].strip()
        return ""

    def _parse_reminder(self, text: str) -> Optional[dict]:
        """Parse reminder from text"""
        text = text.lower()

        for trigger in ['remind me to', 'remind me about', 'set a reminder to', 'set reminder']:
            if trigger in text:
                rest = text.split(trigger, 1)[1].strip()

                time_markers = [' at ', ' in ', ' tomorrow', ' tonight']
                for marker in time_markers:
                    if marker in rest:
                        parts = rest.split(marker, 1)
                        message = parts[0].strip()
                        time_str = marker.strip() + ' ' + parts[1].strip() if len(parts) > 1 else marker.strip()
                        return {'message': message, 'time': time_str.strip()}

                return {'message': rest, 'time': 'in 1 hour'}

        return None

    def stop(self):
        """Stop the voice interface"""
        print("\nShutting down A.R.T.H.U.R...")
        self.is_active = False
        self.reminders.stop_checker()
        self.ears.stop_listening()
        self.voice.speak("Goodbye, sir. A.R.T.H.U.R. signing off.")
        print("Shutdown complete.")
