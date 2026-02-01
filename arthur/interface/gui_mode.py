"""
ARTHUR JARVIS-Style GUI Interface
Inspired by Concept Bytes' JARVIS designs
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import Canvas
import threading
import math
import time
import random
from datetime import datetime
from typing import Optional
from ..core.brain import Brain
from ..core.voice import Voice, VoiceMode
from ..core.memory import Memory
from ..core.ears import Ears
from ..features.tasks import TaskManager
from ..features.schedule import ScheduleManager
from ..features.reminders import ReminderManager
from ..features.study import StudyTimer
from ..features.weather import WeatherService
from ..features.planner import PlanningAssistant
from ..features.notion import NotionIntegration
from ..features.git_projects import GitProjectsManager
from ..features.google_calendar import GoogleCalendarIntegration


# JARVIS Color Scheme
COLORS = {
    'bg': '#000000',
    'bg_dark': '#0a0a0a',
    'cyan': '#00f0ff',
    'cyan_dim': '#006670',
    'cyan_glow': '#00f0ff',
    'blue': '#0066ff',
    'text': '#ffffff',
    'text_dim': '#888888',
    'accent': '#00f0ff',
    'warning': '#ff6600',
    'success': '#00ff66',
}


class ArcReactor(Canvas):
    """Animated Arc Reactor visualization"""

    def __init__(self, parent, size=200, **kwargs):
        super().__init__(parent, width=size, height=size, bg=COLORS['bg'],
                         highlightthickness=0, **kwargs)
        self.size = size
        self.center = size // 2
        self.angle = 0
        self.pulse = 0
        self.is_thinking = False
        self.is_speaking = False
        self.draw_reactor()
        self.animate()

    def draw_reactor(self):
        self.delete("all")
        c = self.center

        # Outer ring
        self.create_oval(10, 10, self.size-10, self.size-10,
                        outline=COLORS['cyan_dim'], width=2)

        # Middle rings with rotation
        for i, radius in enumerate([70, 55, 40]):
            offset = self.angle * (i + 1) * 0.5
            self.draw_arc_segments(c, c, radius, offset, 6 - i)

        # Inner core with pulse effect
        pulse_size = 25 + math.sin(self.pulse) * 5
        glow_intensity = 0.5 + math.sin(self.pulse) * 0.3

        # Core glow
        for i in range(3):
            size = pulse_size + i * 5
            alpha = int(255 * glow_intensity * (1 - i * 0.3))
            self.create_oval(c - size, c - size, c + size, c + size,
                           outline=COLORS['cyan'], width=2 - i * 0.5)

        # Center dot
        self.create_oval(c - 8, c - 8, c + 8, c + 8,
                        fill=COLORS['cyan'], outline='')

        # Status indicator
        if self.is_thinking:
            self.draw_thinking_indicator()
        elif self.is_speaking:
            self.draw_speaking_indicator()

    def draw_arc_segments(self, x, y, radius, offset, segments):
        """Draw segmented arc ring"""
        segment_angle = 360 / segments
        gap = 15

        for i in range(segments):
            start = i * segment_angle + offset
            extent = segment_angle - gap

            x0 = x - radius
            y0 = y - radius
            x1 = x + radius
            y1 = y + radius

            self.create_arc(x0, y0, x1, y1, start=start, extent=extent,
                          outline=COLORS['cyan'], width=2, style='arc')

    def draw_thinking_indicator(self):
        """Pulsing indicator when processing"""
        c = self.center
        for i in range(4):
            angle = self.angle * 3 + i * 90
            x = c + math.cos(math.radians(angle)) * 85
            y = c + math.sin(math.radians(angle)) * 85
            size = 4 + math.sin(self.pulse + i) * 2
            self.create_oval(x - size, y - size, x + size, y + size,
                           fill=COLORS['cyan'], outline='')

    def draw_speaking_indicator(self):
        """Waveform indicator when speaking"""
        c = self.center
        for i in range(8):
            angle = i * 45
            wave = math.sin(self.pulse * 2 + i) * 10
            x = c + math.cos(math.radians(angle)) * (85 + wave)
            y = c + math.sin(math.radians(angle)) * (85 + wave)
            self.create_oval(x - 3, y - 3, x + 3, y + 3,
                           fill=COLORS['cyan'], outline='')

    def animate(self):
        self.angle += 1
        self.pulse += 0.1
        self.draw_reactor()
        self.after(50, self.animate)

    def set_thinking(self, thinking: bool):
        self.is_thinking = thinking
        self.is_speaking = False

    def set_speaking(self, speaking: bool):
        self.is_speaking = speaking
        self.is_thinking = False


class WaveformVisualizer(Canvas):
    """Audio waveform visualization"""

    def __init__(self, parent, width=400, height=60, **kwargs):
        super().__init__(parent, width=width, height=height, bg=COLORS['bg'],
                        highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.bars = 40
        self.values = [0.1] * self.bars
        self.target_values = [0.1] * self.bars
        self.active = False
        self.animate()

    def set_active(self, active: bool):
        self.active = active
        if active:
            self.randomize()

    def randomize(self):
        if self.active:
            self.target_values = [random.uniform(0.2, 1.0) for _ in range(self.bars)]
            self.after(100, self.randomize)
        else:
            self.target_values = [0.1] * self.bars

    def animate(self):
        self.delete("all")

        bar_width = self.width / self.bars

        for i in range(self.bars):
            # Smooth interpolation
            self.values[i] += (self.target_values[i] - self.values[i]) * 0.3

            bar_height = self.values[i] * self.height * 0.8
            x = i * bar_width
            y_top = (self.height - bar_height) / 2
            y_bottom = y_top + bar_height

            # Draw bar with gradient effect
            self.create_rectangle(
                x + 2, y_top,
                x + bar_width - 2, y_bottom,
                fill=COLORS['cyan'], outline=''
            )

        self.after(50, self.animate)


class HUDPanel(ctk.CTkFrame):
    """JARVIS-style HUD information panel"""

    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, fg_color=COLORS['bg'], corner_radius=0, **kwargs)

        # Border effect
        self.configure(border_width=1, border_color=COLORS['cyan_dim'])

        # Title
        if title:
            title_frame = ctk.CTkFrame(self, fg_color=COLORS['bg'], corner_radius=0)
            title_frame.pack(fill='x', padx=2, pady=2)

            ctk.CTkLabel(
                title_frame, text=f"[ {title} ]",
                font=("Courier New", 10),
                text_color=COLORS['cyan']
            ).pack(anchor='w', padx=5)

        self.content_frame = ctk.CTkFrame(self, fg_color=COLORS['bg'], corner_radius=0)
        self.content_frame.pack(fill='both', expand=True, padx=5, pady=5)


class GUIInterface(ctk.CTk):
    """JARVIS-style GUI interface for ARTHUR"""

    def __init__(self, config: dict = None):
        super().__init__()

        config = config or {}

        # Window setup
        self.title("A.R.T.H.U.R.")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=COLORS['bg'])

        # Initialize core systems
        self.memory = Memory()
        self.brain = Brain(model=config.get('model', 'llama3.2:latest'))

        # Initialize voice with ElevenLabs if API key provided
        elevenlabs_key = config.get('elevenlabs_api_key')
        if elevenlabs_key:
            self.voice = Voice(
                mode=VoiceMode.ELEVENLABS,
                elevenlabs_api_key=elevenlabs_key,
                voice_id=config.get('elevenlabs_voice_id', 'fTPiybpX1pEUiksgLZnP')
            )
        else:
            self.voice = Voice(mode=VoiceMode.OFFLINE)
        self.voice_enabled = config.get('voice_enabled', True)

        # Initialize features
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

        # Notion integration
        self.notion = NotionIntegration(
            api_key=config.get('notion_api_key'),
            calendar_db_id=config.get('notion_calendar_db')
        )

        # Google Calendar integration
        self.google_calendar = GoogleCalendarIntegration()

        # Git projects integration
        project_paths = config.get('git_project_paths', [])
        self.git_projects = GitProjectsManager(project_paths)

        # Initialize speech recognition
        self.ears = None
        self.is_voice_recording = False
        self._init_ears()

        self._setup_ui()
        self._start_clock()

        # Start reminder checker
        self.reminders.start_checker()

        # Initial greeting
        self.after(500, self._initial_greeting)

    def _setup_ui(self):
        """Set up the JARVIS-style interface"""
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS['bg'], corner_radius=0)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Top bar with system info
        self._setup_top_bar()

        # Main content area
        content_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg'], corner_radius=0)
        content_frame.pack(fill='both', expand=True, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_columnconfigure(2, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left panel - Arc Reactor and status
        self._setup_left_panel(content_frame)

        # Center panel - Chat/conversation
        self._setup_center_panel(content_frame)

        # Right panel - Quick info
        self._setup_right_panel(content_frame)

        # Bottom bar - Input
        self._setup_bottom_bar()

    def _setup_top_bar(self):
        """Top bar with system status"""
        top_bar = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg'], height=40, corner_radius=0)
        top_bar.pack(fill='x', pady=(0, 10))
        top_bar.pack_propagate(False)

        # Left side - ARTHUR title
        title_label = ctk.CTkLabel(
            top_bar,
            text="A.R.T.H.U.R.",
            font=("Courier New", 24, "bold"),
            text_color=COLORS['cyan']
        )
        title_label.pack(side='left')

        subtitle = ctk.CTkLabel(
            top_bar,
            text="  //  Advanced Real-Time Helper & Understanding Resource",
            font=("Courier New", 11),
            text_color=COLORS['text_dim']
        )
        subtitle.pack(side='left', padx=10)

        # Right side - Clock
        self.clock_label = ctk.CTkLabel(
            top_bar,
            text="",
            font=("Courier New", 14),
            text_color=COLORS['cyan']
        )
        self.clock_label.pack(side='right')

        # Status indicator
        self.status_label = ctk.CTkLabel(
            top_bar,
            text="[ ONLINE ]",
            font=("Courier New", 11),
            text_color=COLORS['success']
        )
        self.status_label.pack(side='right', padx=20)

    def _setup_left_panel(self, parent):
        """Left panel with Arc Reactor"""
        left_panel = ctk.CTkFrame(parent, fg_color=COLORS['bg'], corner_radius=0)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        # Arc Reactor
        self.arc_reactor = ArcReactor(left_panel, size=200)
        self.arc_reactor.pack(pady=20)

        # Waveform visualizer
        self.waveform = WaveformVisualizer(left_panel, width=200, height=50)
        self.waveform.pack(pady=10)

        # Quick actions panel
        actions_panel = HUDPanel(left_panel, title="QUICK ACTIONS")
        actions_panel.pack(fill='x', pady=20, padx=10)

        quick_actions = [
            ("DAILY BRIEFING", "give me my daily briefing"),
            ("VIEW TASKS", "view tasks"),
            ("START FOCUS", "start focus session"),
            ("STUDY STATS", "study statistics"),
        ]

        for label, command in quick_actions:
            btn = ctk.CTkButton(
                actions_panel.content_frame,
                text=label,
                font=("Courier New", 10),
                fg_color=COLORS['bg'],
                border_width=1,
                border_color=COLORS['cyan_dim'],
                hover_color=COLORS['cyan_dim'],
                text_color=COLORS['cyan'],
                height=30,
                corner_radius=0,
                command=lambda c=command: self._quick_command(c)
            )
            btn.pack(fill='x', pady=2)

    def _setup_center_panel(self, parent):
        """Center panel with conversation"""
        center_panel = ctk.CTkFrame(parent, fg_color=COLORS['bg'], corner_radius=0,
                                    border_width=1, border_color=COLORS['cyan_dim'])
        center_panel.grid(row=0, column=1, sticky='nsew', padx=10)

        # Header
        header = ctk.CTkFrame(center_panel, fg_color=COLORS['bg'], height=30, corner_radius=0)
        header.pack(fill='x', padx=10, pady=5)

        ctk.CTkLabel(
            header,
            text="[ COMMUNICATION INTERFACE ]",
            font=("Courier New", 10),
            text_color=COLORS['cyan']
        ).pack(side='left')

        # Chat display
        self.chat_display = ctk.CTkTextbox(
            center_panel,
            font=("Courier New", 12),
            fg_color=COLORS['bg'],
            text_color=COLORS['text'],
            border_width=0,
            corner_radius=0,
            wrap='word'
        )
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=5)
        self.chat_display.configure(state='disabled')

        # Configure tags for colored text
        self.chat_display._textbox.tag_configure('arthur', foreground=COLORS['cyan'])
        self.chat_display._textbox.tag_configure('user', foreground=COLORS['text'])
        self.chat_display._textbox.tag_configure('system', foreground=COLORS['text_dim'])
        self.chat_display._textbox.tag_configure('timestamp', foreground=COLORS['cyan_dim'])

    def _setup_right_panel(self, parent):
        """Right panel with system info"""
        right_panel = ctk.CTkFrame(parent, fg_color=COLORS['bg'], corner_radius=0)
        right_panel.grid(row=0, column=2, sticky='nsew', padx=(10, 0))

        # Create scrollable frame for panels
        scroll_frame = ctk.CTkScrollableFrame(right_panel, fg_color=COLORS['bg'])
        scroll_frame.pack(fill='both', expand=True)

        # Timer panel
        timer_panel = HUDPanel(scroll_frame, title="FOCUS TIMER")
        timer_panel.pack(fill='x', pady=(0, 8), padx=5)

        self.timer_label = ctk.CTkLabel(
            timer_panel.content_frame,
            text="--:--",
            font=("Courier New", 28, "bold"),
            text_color=COLORS['cyan']
        )
        self.timer_label.pack(pady=5)

        self.timer_status = ctk.CTkLabel(
            timer_panel.content_frame,
            text="NO ACTIVE SESSION",
            font=("Courier New", 9),
            text_color=COLORS['text_dim']
        )
        self.timer_status.pack()

        # Google Calendar panel
        calendar_panel = HUDPanel(scroll_frame, title="CALENDAR")
        calendar_panel.pack(fill='x', pady=8, padx=5)

        self.calendar_display = ctk.CTkLabel(
            calendar_panel.content_frame,
            text="Not connected",
            font=("Courier New", 9),
            text_color=COLORS['text'],
            justify='left',
            anchor='w',
            wraplength=180
        )
        self.calendar_display.pack(fill='x', anchor='w')

        # Git Projects panel
        git_panel = HUDPanel(scroll_frame, title="GIT PROJECTS")
        git_panel.pack(fill='x', pady=8, padx=5)

        self.git_display = ctk.CTkLabel(
            git_panel.content_frame,
            text="Scanning...",
            font=("Courier New", 9),
            text_color=COLORS['text'],
            justify='left',
            anchor='w',
            wraplength=180
        )
        self.git_display.pack(fill='x', anchor='w')

        # Tasks panel
        tasks_panel = HUDPanel(scroll_frame, title="ACTIVE TASKS")
        tasks_panel.pack(fill='x', pady=8, padx=5)

        self.tasks_display = ctk.CTkLabel(
            tasks_panel.content_frame,
            text="Loading...",
            font=("Courier New", 9),
            text_color=COLORS['text'],
            justify='left',
            anchor='w',
            wraplength=180
        )
        self.tasks_display.pack(fill='x', anchor='w')

        # System panel
        system_panel = HUDPanel(scroll_frame, title="SYSTEM")
        system_panel.pack(fill='x', pady=8, padx=5)

        self.voice_toggle = ctk.CTkButton(
            system_panel.content_frame,
            text=f"VOICE: {'ON' if self.voice_enabled else 'OFF'}",
            font=("Courier New", 9),
            fg_color=COLORS['bg'],
            border_width=1,
            border_color=COLORS['success'] if self.voice_enabled else COLORS['warning'],
            hover_color=COLORS['cyan_dim'],
            text_color=COLORS['success'] if self.voice_enabled else COLORS['warning'],
            height=22,
            corner_radius=0,
            command=self._toggle_voice
        )
        self.voice_toggle.pack(fill='x', pady=2)

        # Update panels periodically
        self._update_info_panels()

    def _setup_bottom_bar(self):
        """Bottom input bar"""
        bottom_bar = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg'], height=50, corner_radius=0)
        bottom_bar.pack(fill='x', pady=(10, 0))
        bottom_bar.pack_propagate(False)

        # Input container
        input_container = ctk.CTkFrame(bottom_bar, fg_color=COLORS['bg'],
                                       border_width=1, border_color=COLORS['cyan_dim'],
                                       corner_radius=0)
        input_container.pack(fill='both', expand=True, padx=50)

        # Prompt indicator
        ctk.CTkLabel(
            input_container,
            text=">",
            font=("Courier New", 16, "bold"),
            text_color=COLORS['cyan']
        ).pack(side='left', padx=10)

        # Input field
        self.input_field = ctk.CTkEntry(
            input_container,
            font=("Courier New", 14),
            fg_color=COLORS['bg'],
            text_color=COLORS['text'],
            border_width=0,
            corner_radius=0,
            placeholder_text="Enter command...",
            placeholder_text_color=COLORS['text_dim']
        )
        self.input_field.pack(side='left', fill='both', expand=True, pady=5)
        self.input_field.bind('<Return>', self._on_send)

        # Send button
        self.send_button = ctk.CTkButton(
            input_container,
            text="TRANSMIT",
            font=("Courier New", 11),
            fg_color=COLORS['cyan_dim'],
            hover_color=COLORS['cyan'],
            text_color=COLORS['bg'],
            width=100,
            height=30,
            corner_radius=0,
            command=self._on_send
        )
        self.send_button.pack(side='right', padx=10, pady=5)

        # Microphone button
        self.mic_button = ctk.CTkButton(
            input_container,
            text="MIC",
            font=("Courier New", 11),
            fg_color=COLORS['bg'],
            border_width=1,
            border_color=COLORS['cyan_dim'],
            hover_color=COLORS['cyan_dim'],
            text_color=COLORS['cyan'],
            width=50,
            height=30,
            corner_radius=0,
            command=self._on_mic_click
        )
        self.mic_button.pack(side='right', padx=5, pady=5)

    def _add_message(self, sender: str, message: str, tag: str = 'user'):
        """Add a message to the chat display"""
        self.chat_display.configure(state='normal')

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Insert timestamp
        self.chat_display._textbox.insert('end', f"[{timestamp}] ", 'timestamp')

        # Insert sender
        if sender == "ARTHUR":
            self.chat_display._textbox.insert('end', f"{sender}: ", 'arthur')
            self.chat_display._textbox.insert('end', f"{message}\n\n", 'arthur')
        else:
            self.chat_display._textbox.insert('end', f"{sender}: ", 'user')
            self.chat_display._textbox.insert('end', f"{message}\n\n", 'user')

        self.chat_display.see('end')
        self.chat_display.configure(state='disabled')

    def _init_ears(self):
        """Initialize speech recognition in background"""
        def init():
            try:
                self.ears = Ears()
                print("Voice input initialized")
            except Exception as e:
                print(f"Voice input init failed: {e}")
                self.ears = None
        threading.Thread(target=init, daemon=True).start()

    def _initial_greeting(self):
        """Display initial greeting"""
        greeting = self.brain.get_greeting()
        self._add_message("ARTHUR", greeting)
        if self.voice_enabled:
            self._speak_async(greeting)

    def _on_send(self, event=None):
        """Handle send button click or Enter key"""
        user_input = self.input_field.get().strip()
        if not user_input:
            return

        self.input_field.delete(0, 'end')
        self._add_message("USER", user_input)
        self.memory.save_conversation("user", user_input)

        # Update UI state
        self.arc_reactor.set_thinking(True)
        self.status_label.configure(text="[ PROCESSING ]", text_color=COLORS['warning'])
        self.send_button.configure(state='disabled')

        # Process in background
        threading.Thread(target=self._process_input, args=(user_input,), daemon=True).start()

    def _on_mic_click(self):
        """Handle microphone button click"""
        if self.ears is None:
            self._add_message("ARTHUR", "Voice input is still initializing. Please try again in a moment.")
            return

        if self.is_voice_recording:
            return

        self.is_voice_recording = True
        self.mic_button.configure(
            text="...",
            fg_color=COLORS['warning'],
            text_color=COLORS['bg']
        )
        self.status_label.configure(text="[ LISTENING ]", text_color=COLORS['warning'])
        self.arc_reactor.set_thinking(True)

        # Listen in background
        threading.Thread(target=self._voice_input_thread, daemon=True).start()

    def _voice_input_thread(self):
        """Handle voice input in background"""
        try:
            text = self.ears.listen_once()
            self.after(0, self._handle_voice_result, text)
        except Exception as e:
            print(f"Voice input error: {e}")
            self.after(0, self._handle_voice_result, "")

    def _handle_voice_result(self, text: str):
        """Process voice input result in main thread"""
        self.is_voice_recording = False
        self.mic_button.configure(
            text="MIC",
            fg_color=COLORS['bg'],
            text_color=COLORS['cyan']
        )
        self.arc_reactor.set_thinking(False)

        if text:
            self.input_field.delete(0, 'end')
            self.input_field.insert(0, text)
            self._on_send()
        else:
            self.status_label.configure(text="[ ONLINE ]", text_color=COLORS['success'])
            self._add_message("ARTHUR", "I didn't catch that. Could you try again?")

    def _process_input(self, user_input: str):
        """Process user input in background thread"""
        response = self._handle_command(user_input)
        self.after(0, self._display_response, response)

    def _display_response(self, response: str):
        """Display response in main thread"""
        self._add_message("ARTHUR", response)
        self.memory.save_conversation("assistant", response)

        # Update UI state
        self.arc_reactor.set_thinking(False)
        self.status_label.configure(text="[ ONLINE ]", text_color=COLORS['success'])
        self.send_button.configure(state='normal')

        # Update info panels
        self._update_info_panels()

        if self.voice_enabled:
            self._speak_async(response)

    def _speak_async(self, text: str):
        """Speak text asynchronously"""
        def speak():
            self.after(0, lambda: self.arc_reactor.set_speaking(True))
            self.after(0, lambda: self.waveform.set_active(True))
            self.voice.speak(text)
            self.after(0, lambda: self.arc_reactor.set_speaking(False))
            self.after(0, lambda: self.waveform.set_active(False))

        threading.Thread(target=speak, daemon=True).start()

    def _handle_command(self, user_input: str) -> str:
        """Process command and return response - AI-first approach"""
        lower_input = user_input.lower()

        # Only intercept very specific action commands
        # Everything else goes to the AI for natural conversation

        # Calendar connection (special case)
        if 'connect' in lower_input and 'calendar' in lower_input:
            if self.google_calendar.authenticate():
                return "Google Calendar connected successfully, sir. I now have access to your schedule."
            else:
                return "Calendar connection failed. Make sure google_credentials.json is in the arthur/data folder."

        # Study timer controls (need immediate action)
        if ('start' in lower_input and ('focus' in lower_input or 'study' in lower_input or 'pomodoro' in lower_input)):
            return self.study.start_session()

        if ('stop' in lower_input and ('focus' in lower_input or 'study' in lower_input or 'session' in lower_input or 'timer' in lower_input)):
            return self.study.stop_session()

        # Build rich context for the AI
        context_parts = []

        # Add tasks
        tasks = self.memory.get_tasks()
        if tasks:
            task_list = ", ".join([t['title'] for t in tasks[:5]])
            context_parts.append(f"Current tasks: {task_list}")

        # Add calendar events
        if self.google_calendar.is_configured():
            events = self.google_calendar.get_upcoming_events(3)
            if events:
                event_list = ", ".join([f"{e['title']}" for e in events[:3]])
                context_parts.append(f"Upcoming calendar events: {event_list}")

        # Add git projects
        if self.git_projects.repos:
            dirty = [name for name, repo in self.git_projects.repos.items()
                    if self.git_projects._is_dirty_safe(repo)]
            if dirty:
                context_parts.append(f"Git projects with uncommitted changes: {', '.join(dirty[:3])}")
            context_parts.append(f"Total git projects: {len(self.git_projects.repos)}")

        # Add study status
        if self.study.is_active:
            remaining = self.study.remaining_seconds // 60
            context_parts.append(f"Active study session: {remaining} minutes remaining")

        # Add assignments
        assignments = self.memory.get_upcoming_assignments(7)
        if assignments:
            assignment_list = ", ".join([f"{a['title']} (due {a['due_date']})" for a in assignments[:3]])
            context_parts.append(f"Upcoming assignments: {assignment_list}")

        # Add class schedule
        next_class = self.memory.get_next_class()
        if next_class:
            context_parts.append(f"Next class: {next_class['title']} at {next_class['start_time']}")

        context = "\n".join(context_parts) if context_parts else "No active items."

        # Enhanced system context for the AI
        action_context = """
You have access to the user's:
- Task list (can add/view/complete tasks)
- Google Calendar (can show events)
- Git projects (can show status, changes)
- Study timer (can start/stop focus sessions)
- Class schedule and assignments

If the user asks to DO something (add task, show calendar, etc.), respond naturally AND confirm what you did.
If they're just chatting or asking questions, have a natural conversation.
Always be helpful, concise, and maintain your JARVIS personality.
"""

        full_context = action_context + "\n\nCurrent Status:\n" + context

        # Let the AI handle the response naturally
        response = self.brain.think(user_input, full_context)

        # Post-process: Check if AI mentioned doing an action, actually do it
        self._execute_mentioned_actions(user_input, lower_input, response)

        return response

    def _execute_mentioned_actions(self, user_input: str, lower_input: str, response: str):
        """Execute actions that the AI mentioned doing"""
        # If user asked to add a task and AI confirmed, actually add it
        if 'add' in lower_input and 'task' in lower_input:
            # Extract task name
            task_name = self._extract_after(lower_input, ['add task', 'add a task', 'new task', 'create task'])
            if task_name:
                self.tasks.add_task(task_name)

        # If user asked to complete a task
        if ('complete' in lower_input or 'finish' in lower_input or 'done' in lower_input) and 'task' in lower_input:
            task_id = self._extract_after(lower_input, ['complete task', 'finish task', 'mark task', 'task'])
            if task_id:
                self.tasks.complete_task(task_id)

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
        self.input_field.delete(0, 'end')
        self.input_field.insert(0, command)
        self._on_send()

    def _toggle_voice(self):
        """Toggle voice output"""
        self.voice_enabled = not self.voice_enabled

        if self.voice_enabled:
            self.voice_toggle.configure(
                text="VOICE: ON",
                border_color=COLORS['success'],
                text_color=COLORS['success']
            )
        else:
            self.voice_toggle.configure(
                text="VOICE: OFF",
                border_color=COLORS['warning'],
                text_color=COLORS['warning']
            )

    def _start_clock(self):
        """Start the clock update"""
        def update():
            now = datetime.now()
            self.clock_label.configure(text=now.strftime("%H:%M:%S  //  %A, %B %d, %Y"))
            self.after(1000, update)
        update()

    def _update_info_panels(self):
        """Update the info panels on the right"""
        # Update tasks
        tasks = self.memory.get_tasks()
        if tasks:
            task_text = "\n".join([f"> {t['title'][:25]}" for t in tasks[:4]])
            if len(tasks) > 4:
                task_text += f"\n(+{len(tasks) - 4} more)"
        else:
            task_text = "No active tasks"
        self.tasks_display.configure(text=task_text)

        # Update Google Calendar
        if self.google_calendar.is_configured():
            events = self.google_calendar.get_upcoming_events(days_ahead=3)
            if events:
                cal_text = "\n".join([f"> {e['title'][:20]}" for e in events[:3]])
                if len(events) > 3:
                    cal_text += f"\n(+{len(events) - 3} more)"
            else:
                cal_text = "No upcoming events"
        else:
            cal_text = "Say 'connect calendar'"
        self.calendar_display.configure(text=cal_text)

        # Update Git projects
        try:
            dirty_count = sum(1 for r in self.git_projects.repos.values()
                            if self.git_projects._is_dirty_safe(r))
            total = len(self.git_projects.repos)

            if total > 0:
                git_text = f"{total} projects tracked"
                if dirty_count > 0:
                    git_text += f"\n{dirty_count} with changes"

                # Show first few project names
                projects = list(self.git_projects.repos.keys())[:3]
                for p in projects:
                    status = "*" if self.git_projects._is_dirty_safe(self.git_projects.repos[p]) else "+"
                    git_text += f"\n{status} {p[:18]}"
            else:
                git_text = "No repos found"
        except:
            git_text = "Scanning..."
        self.git_display.configure(text=git_text)

        # Schedule next update
        self.after(30000, self._update_info_panels)

    def _on_reminder(self, message: str):
        """Handle reminder notification"""
        self.after(0, self._add_message, "ARTHUR", message)
        if self.voice_enabled:
            self._speak_async(message)

    def _on_study_complete(self, pomodoro_count: int, break_duration: int):
        """Handle study session completion"""
        message = f"Session complete. {pomodoro_count} pomodoro(s) logged. I recommend a {break_duration}-minute break, sir."
        self.after(0, self._add_message, "ARTHUR", message)
        self.after(0, self._update_timer_display, "--:--", "SESSION COMPLETE")
        if self.voice_enabled:
            self._speak_async(message)

    def _on_break_complete(self):
        """Handle break completion"""
        message = "Break concluded. Ready to resume operations when you are, sir."
        self.after(0, self._add_message, "ARTHUR", message)
        self.after(0, self._update_timer_display, "--:--", "NO ACTIVE SESSION")
        if self.voice_enabled:
            self._speak_async(message)

    def _on_timer_tick(self, remaining_seconds: int, is_break: bool):
        """Update timer display"""
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        status = "BREAK MODE" if is_break else "FOCUS MODE"
        self.after(0, self._update_timer_display, time_str, status)

    def _update_timer_display(self, time_str: str, status: str):
        """Update timer label in main thread"""
        self.timer_label.configure(text=time_str)
        self.timer_status.configure(text=status)

    def run(self):
        """Start the GUI"""
        self.mainloop()

    def on_closing(self):
        """Handle window close"""
        self.reminders.stop_checker()
        self.destroy()
