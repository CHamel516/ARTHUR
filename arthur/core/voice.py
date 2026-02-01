"""
ARTHUR's Voice - Text-to-Speech Output
Supports ElevenLabs (high quality) and pyttsx3 (offline fallback)
"""

import pyttsx3
import tempfile
import os
import subprocess
from typing import Optional
from enum import Enum


class VoiceMode(Enum):
    OFFLINE = "offline"
    ELEVENLABS = "elevenlabs"


class Voice:
    """Handles all speech output for ARTHUR"""

    # Default ElevenLabs voice ID - can be overridden
    ELEVENLABS_VOICE_ID = "fTPiybpX1pEUiksgLZnP"

    def __init__(self, mode: VoiceMode = VoiceMode.ELEVENLABS,
                 elevenlabs_api_key: Optional[str] = None,
                 voice_id: Optional[str] = None):
        """
        Initialize text-to-speech

        Args:
            mode: VoiceMode.ELEVENLABS for high quality, VoiceMode.OFFLINE for pyttsx3
            elevenlabs_api_key: API key for ElevenLabs
            voice_id: Custom ElevenLabs voice ID
        """
        self.mode = mode
        self.elevenlabs_api_key = elevenlabs_api_key
        self.voice_id = voice_id or self.ELEVENLABS_VOICE_ID
        self.engine: Optional[pyttsx3.Engine] = None
        self.elevenlabs_client = None
        self.is_speaking = False

        if mode == VoiceMode.ELEVENLABS and elevenlabs_api_key:
            self._init_elevenlabs()
        else:
            self._init_offline_engine()

    def _init_elevenlabs(self):
        """Initialize ElevenLabs client"""
        try:
            from elevenlabs.client import ElevenLabs
            self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)
            print("ElevenLabs voice initialized")
        except Exception as e:
            print(f"ElevenLabs init failed: {e}, falling back to offline")
            self._init_offline_engine()
            self.mode = VoiceMode.OFFLINE

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
            if self.mode == VoiceMode.ELEVENLABS and self.elevenlabs_client:
                self._speak_elevenlabs(text)
            else:
                self._speak_offline(text)
        except Exception as e:
            print(f"TTS error: {e}")
            # Fallback to offline
            if self.mode == VoiceMode.ELEVENLABS:
                print("Falling back to offline TTS...")
                self._speak_offline(text)

        self.is_speaking = False

    def _speak_elevenlabs(self, text: str):
        """Speak using ElevenLabs"""
        try:
            from elevenlabs import play

            audio = self.elevenlabs_client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_turbo_v2_5"
            )

            # Collect the audio bytes
            audio_bytes = b"".join(audio)

            # Save to temp file and play
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name

            try:
                subprocess.run(['afplay', temp_path], check=True, capture_output=True)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            print(f"ElevenLabs error: {e}")
            raise

    def _speak_offline(self, text: str):
        """Speak using pyttsx3 (offline)"""
        if self.engine is None:
            self._init_offline_engine()

        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

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
        Switch between offline and ElevenLabs mode

        Args:
            mode: VoiceMode to switch to
        """
        self.mode = mode
        if mode == VoiceMode.OFFLINE and self.engine is None:
            self._init_offline_engine()

    def set_voice_id(self, voice_id: str):
        """Set ElevenLabs voice ID"""
        self.voice_id = voice_id

    def test(self):
        """Test the TTS system"""
        self.speak("A.R.T.H.U.R. voice systems online and operational, sir.")
