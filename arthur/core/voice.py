"""
ARTHUR's Voice - Text-to-Speech Output
Supports both offline (pyttsx3) and high-quality (edge-tts) synthesis
"""

import pyttsx3
import asyncio
import tempfile
import os
import subprocess
from typing import Optional
from enum import Enum


class VoiceMode(Enum):
    OFFLINE = "offline"
    HIGH_QUALITY = "high_quality"


class Voice:
    """Handles all speech output for ARTHUR"""

    EDGE_VOICE = "en-GB-RyanNeural"

    def __init__(self, mode: VoiceMode = VoiceMode.OFFLINE):
        """
        Initialize text-to-speech

        Args:
            mode: VoiceMode.OFFLINE for pyttsx3, VoiceMode.HIGH_QUALITY for edge-tts
        """
        self.mode = mode
        self.engine: Optional[pyttsx3.Engine] = None
        self.is_speaking = False

        if mode == VoiceMode.OFFLINE:
            self._init_offline_engine()

    def _init_offline_engine(self):
        """Initialize pyttsx3 for offline TTS"""
        try:
            self.engine = pyttsx3.init()

            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'english' in voice.name.lower() and ('uk' in voice.name.lower() or 'british' in voice.name.lower()):
                    self.engine.setProperty('voice', voice.id)
                    break

            self.engine.setProperty('rate', 175)
            self.engine.setProperty('volume', 0.9)

            print("Offline TTS engine initialized")
        except Exception as e:
            print(f"Error initializing pyttsx3: {e}")

    def speak(self, text: str):
        """
        Speak the given text

        Args:
            text: Text to speak
        """
        if not text:
            return

        self.is_speaking = True

        try:
            if self.mode == VoiceMode.HIGH_QUALITY:
                asyncio.run(self._speak_edge_tts(text))
            else:
                self._speak_offline(text)
        except Exception as e:
            print(f"TTS error: {e}")
            if self.mode == VoiceMode.HIGH_QUALITY:
                print("Falling back to offline TTS...")
                self._speak_offline(text)

        self.is_speaking = False

    def _speak_offline(self, text: str):
        """Speak using pyttsx3 (offline)"""
        if self.engine is None:
            self._init_offline_engine()

        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

    async def _speak_edge_tts(self, text: str):
        """Speak using edge-tts (high quality, requires internet)"""
        import edge_tts

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            temp_path = f.name

        try:
            communicate = edge_tts.Communicate(text, self.EDGE_VOICE)
            await communicate.save(temp_path)

            if os.path.exists(temp_path):
                subprocess.run(
                    ['afplay', temp_path],
                    check=True,
                    capture_output=True
                )
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def speak_async(self, text: str):
        """
        Speak text without blocking (runs in background)

        Args:
            text: Text to speak
        """
        import threading
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()

    def stop(self):
        """Stop current speech"""
        self.is_speaking = False
        if self.engine:
            self.engine.stop()

    def set_mode(self, mode: VoiceMode):
        """
        Switch between offline and high-quality mode

        Args:
            mode: VoiceMode to switch to
        """
        self.mode = mode
        if mode == VoiceMode.OFFLINE and self.engine is None:
            self._init_offline_engine()

    def set_rate(self, rate: int):
        """
        Set speech rate (words per minute)

        Args:
            rate: Speech rate (default ~175)
        """
        if self.engine:
            self.engine.setProperty('rate', rate)

    def set_volume(self, volume: float):
        """
        Set speech volume

        Args:
            volume: Volume from 0.0 to 1.0
        """
        if self.engine:
            self.engine.setProperty('volume', max(0.0, min(1.0, volume)))

    def list_voices(self):
        """List available voices for offline mode"""
        if self.engine is None:
            self._init_offline_engine()

        if self.engine:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                print(f"ID: {voice.id}")
                print(f"Name: {voice.name}")
                print(f"Languages: {voice.languages}")
                print("---")

    def test(self):
        """Test the TTS system"""
        self.speak("A.R.T.H.U.R. voice system online and operational, sir.")
