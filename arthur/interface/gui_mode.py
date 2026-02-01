"""
ARTHUR GUI Mode Interface
Modern GUI using CustomTkinter
"""

import customtkinter as ctk
import threading
from datetime import datetime
from typing import Optional
from ..core.brain import Brain
from ..core.voice import Voice, VoiceMode
from ..core.memory import Memory
from ..features.tasks import TaskManager
from ..features.schedule import ScheduleManager
from ..features.reminders import ReminderManager
from ..features.study import StudyTimer
from ..features.weather import WeatherService
from ..features.planner import PlanningAssistant


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GUIInterface(ctk.CTk):
    """GUI interface for ARTHUR using CustomTkinter"""

    def __init__(self, config: dict = None):
        super().__init__()

        config = config or {}

        self.title("A.R.T.H.U.R.")
        self.geometry("900x700")
        self.minsize(700, 500)

        self.memory = Memory()
        self.brain = Brain(model=config.get('model', 'llama3.2:8b'))

        voice_mode = VoiceMode.HIGH_QUALITY if config.get('high_quality_voice') else VoiceMode.OFFLINE
        self.voice = Voice(mode=voice_mode)
        self.voice_enabled = config.get('voice_enabled', True)

        self.tasks = TaskManager(self.memory)
        self.schedule = ScheduleManager(self.memory)
        self.reminders = ReminderManager(self.memory, self._on_reminder)
        self.study = StudyTimer(
            self.memory,
            on_session_complete=self._on_study_complete,
            on_break_complete=self._on_break_complete,
            on_tick=self._on_timer_tick
        )
        self.weather = WeatherService(
            api_key=config.get('weather_api_key'),
            default_city=config.get('default_city', '')
        )
        self.planner = PlanningAssistant(self.memory, self.brain)

        self._setup_ui()
        self._load_conversation_history()

        self.reminders.start_checker()

        greeting = self.brain.get_greeting()
        self._add_message("ARTHUR", greeting)
        if self.voice_enabled:
            threading.Thread(target=self.voice.speak, args=(greeting,), daemon=True).start()

    def _setup_ui(self):
        """Set up the user interface"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self._setup_chat_panel()
        self._setup_sidebar()

    def _setup_chat_panel(self):
        """Set up the main chat panel"""
        chat_frame = ctk.CTkFrame(self.main_frame)
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            wrap="word",
            font=("SF Mono", 13),
            state="disabled"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type a message or command...",
            font=("SF Mono", 13),
            height=40
        )
        self.input_field.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_field.bind("<Return>", self._on_send)

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            width=80,
            height=40,
            command=self._on_send
        )
        self.send_button.grid(row=0, column=1)

        self.voice_button = ctk.CTkButton(
            input_frame,
            text="Voice",
            width=80,
            height=40,
            fg_color="#2d5a2d" if self.voice_enabled else "#5a2d2d",
            command=self._toggle_voice
        )
        self.voice_button.grid(row=0, column=2, padx=(10, 0))

    def _setup_sidebar(self):
        """Set up the sidebar with quick actions and info"""
        sidebar = ctk.CTkFrame(self.main_frame)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        sidebar.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            sidebar,
            text="A.R.T.H.U.R.",
            font=("SF Mono", 18, "bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 5))

        subtitle_label = ctk.CTkLabel(
            sidebar,
            text="AI Assistant",
            font=("SF Mono", 11),
            text_color="gray"
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 15))

        timer_frame = ctk.CTkFrame(sidebar)
        timer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        timer_frame.grid_columnconfigure(0, weight=1)

        self.timer_label = ctk.CTkLabel(
            timer_frame,
            text="No active session",
            font=("SF Mono", 12)
        )
        self.timer_label.grid(row=0, column=0, pady=5)

        timer_buttons = ctk.CTkFrame(timer_frame, fg_color="transparent")
        timer_buttons.grid(row=1, column=0, pady=5)

        ctk.CTkButton(
            timer_buttons,
            text="Start Focus",
            width=80,
            height=30,
            command=lambda: self._quick_command("start focus session")
        ).grid(row=0, column=0, padx=2)

        ctk.CTkButton(
            timer_buttons,
            text="Stop",
            width=60,
            height=30,
            fg_color="#5a2d2d",
            command=lambda: self._quick_command("stop session")
        ).grid(row=0, column=1, padx=2)

        quick_frame = ctk.CTkFrame(sidebar)
        quick_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        quick_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            quick_frame,
            text="Quick Actions",
            font=("SF Mono", 12, "bold")
        ).grid(row=0, column=0, pady=5)

        quick_actions = [
            ("Daily Briefing", "give me my daily briefing"),
            ("View Tasks", "view tasks"),
            ("View Schedule", "view schedule"),
            ("View Assignments", "view assignments"),
            ("Study Stats", "study statistics"),
        ]

        for i, (label, command) in enumerate(quick_actions):
            ctk.CTkButton(
                quick_frame,
                text=label,
                height=30,
                command=lambda c=command: self._quick_command(c)
            ).grid(row=i+1, column=0, sticky="ew", padx=5, pady=2)

        self.status_label = ctk.CTkLabel(
            sidebar,
            text="Ready",
            font=("SF Mono", 10),
            text_color="gray"
        )
        self.status_label.grid(row=4, column=0, pady=10, sticky="s")

    def _add_message(self, sender: str, message: str):
        """Add a message to the chat display"""
        self.chat_display.configure(state="normal")

        timestamp = datetime.now().strftime("%H:%M")
        formatted = f"[{timestamp}] {sender}:\n{message}\n\n"

        self.chat_display.insert("end", formatted)
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _on_send(self, event=None):
        """Handle send button click or Enter key"""
        user_input = self.input_field.get().strip()
        if not user_input:
            return

        self.input_field.delete(0, "end")
        self._add_message("You", user_input)
        self.memory.save_conversation("user", user_input)

        self.status_label.configure(text="Thinking...")
        self.send_button.configure(state="disabled")

        threading.Thread(target=self._process_input, args=(user_input,), daemon=True).start()

    def _process_input(self, user_input: str):
        """Process user input in background thread"""
        response = self._handle_command(user_input)

        self.after(0, self._display_response, response)

    def _display_response(self, response: str):
        """Display response in main thread"""
        self._add_message("ARTHUR", response)
        self.memory.save_conversation("assistant", response)

        self.status_label.configure(text="Ready")
        self.send_button.configure(state="normal")

        if self.voice_enabled:
            threading.Thread(target=self.voice.speak, args=(response,), daemon=True).start()

    def _handle_command(self, user_input: str) -> str:
        """Process command and return response"""
        lower_input = user_input.lower()

        intent = self.brain.analyze_intent(user_input)
        intent_type = intent.get('intent', 'chat')
        entities = intent.get('entities', {})

        if intent_type == 'task_add':
            task_name = entities.get('task_name') or self._extract_after(lower_input, ['add task', 'new task'])
            if task_name:
                return self.tasks.add_task(task_name)

        elif intent_type == 'task_view':
            return self.tasks.view_tasks()

        elif intent_type == 'task_remove':
            task_id = entities.get('task_name') or self._extract_after(lower_input, ['remove task', 'complete task'])
            if task_id:
                if 'complete' in lower_input:
                    return self.tasks.complete_task(task_id)
                return self.tasks.remove_task(task_id)

        elif intent_type == 'schedule_view':
            if 'next class' in lower_input:
                return self.schedule.get_next_class()
            return self.schedule.view_schedule()

        elif intent_type == 'assignment_view':
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
            city = entities.get('location')
            return self.weather.get_weather(city)

        elif intent_type == 'planning':
            if 'briefing' in lower_input:
                return self.planner.get_daily_briefing()
            elif 'prioritize' in lower_input:
                return self.planner.prioritize_tasks()

        if 'study stats' in lower_input or 'study statistics' in lower_input:
            return self.study.get_study_stats()

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
        for trigger in ['remind me to', 'remind me about', 'set reminder']:
            if trigger in text:
                rest = text.split(trigger, 1)[1].strip()
                for marker in [' at ', ' in ']:
                    if marker in rest:
                        parts = rest.split(marker, 1)
                        return {'message': parts[0].strip(), 'time': marker.strip() + ' ' + parts[1]}
                return {'message': rest, 'time': 'in 1 hour'}
        return None

    def _quick_command(self, command: str):
        """Execute a quick command"""
        self.input_field.delete(0, "end")
        self.input_field.insert(0, command)
        self._on_send()

    def _toggle_voice(self):
        """Toggle voice output"""
        self.voice_enabled = not self.voice_enabled
        color = "#2d5a2d" if self.voice_enabled else "#5a2d2d"
        self.voice_button.configure(fg_color=color)

        status = "enabled" if self.voice_enabled else "disabled"
        self._add_message("ARTHUR", f"Voice output {status}.")

    def _on_reminder(self, message: str):
        """Handle reminder notification"""
        self.after(0, self._add_message, "ARTHUR", message)
        if self.voice_enabled:
            threading.Thread(target=self.voice.speak, args=(message,), daemon=True).start()

    def _on_study_complete(self, pomodoro_count: int, break_duration: int):
        """Handle study session completion"""
        message = f"Session complete! {pomodoro_count} pomodoro(s) today. Time for a {break_duration}-minute break."
        self.after(0, self._add_message, "ARTHUR", message)
        self.after(0, self._update_timer_label, "Session complete!")
        if self.voice_enabled:
            threading.Thread(target=self.voice.speak, args=(message,), daemon=True).start()

    def _on_break_complete(self):
        """Handle break completion"""
        message = "Break over. Ready to resume when you are."
        self.after(0, self._add_message, "ARTHUR", message)
        self.after(0, self._update_timer_label, "No active session")
        if self.voice_enabled:
            threading.Thread(target=self.voice.speak, args=(message,), daemon=True).start()

    def _on_timer_tick(self, remaining_seconds: int, is_break: bool):
        """Update timer display"""
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        label = "Break" if is_break else "Focus"
        self.after(0, self._update_timer_label, f"{label}: {minutes}:{seconds:02d}")

    def _update_timer_label(self, text: str):
        """Update timer label in main thread"""
        self.timer_label.configure(text=text)

    def _load_conversation_history(self):
        """Load recent conversation history"""
        history = self.memory.get_recent_conversations(10)
        for msg in history:
            sender = "You" if msg['role'] == 'user' else "ARTHUR"
            self._add_message(sender, msg['content'])

    def run(self):
        """Start the GUI"""
        self.mainloop()

    def on_closing(self):
        """Handle window close"""
        self.reminders.stop_checker()
        self.destroy()
