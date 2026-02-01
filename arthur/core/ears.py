"""
ARTHUR's Ears - Speech Recognition
Uses macOS native speech recognition (offline, fast on Apple Silicon)
Falls back to SpeechRecognition library if needed
"""

import numpy as np
import sounddevice as sd
import queue
import threading
from typing import Optional, Callable

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False


class Ears:
    """Handles all audio input and speech recognition for ARTHUR"""

    WAKE_WORD = "arthur"

    def __init__(self):
        """Initialize speech recognition"""
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_recording = False

        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 0.5
        self.silence_threshold = 0.01
        self.silence_duration = 1.5
        self.max_recording_duration = 30

        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.microphone = sr.Microphone(sample_rate=self.sample_rate)

            with self.microphone as source:
                print("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Microphone calibrated.")
        else:
            print("Warning: SpeechRecognition not available")
            self.recognizer = None
            self.microphone = None

    def _get_audio_level(self, audio_data: np.ndarray) -> float:
        """Calculate RMS audio level"""
        return np.sqrt(np.mean(audio_data ** 2))

    def record_audio(self, max_duration: Optional[float] = None) -> np.ndarray:
        """
        Record audio until silence is detected

        Args:
            max_duration: Maximum recording duration in seconds

        Returns:
            Recorded audio as numpy array
        """
        max_duration = max_duration or self.max_recording_duration
        recorded_chunks = []
        silence_chunks = 0
        chunks_for_silence = int(self.silence_duration / self.chunk_duration)
        max_chunks = int(max_duration / self.chunk_duration)

        self.is_recording = True
        chunk_samples = int(self.sample_rate * self.chunk_duration)

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            self.audio_queue.put(indata.copy())

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            blocksize=chunk_samples,
            callback=audio_callback
        ):
            while self.is_recording and len(recorded_chunks) < max_chunks:
                try:
                    audio_chunk = self.audio_queue.get(timeout=1.0)
                    recorded_chunks.append(audio_chunk)

                    level = self._get_audio_level(audio_chunk)
                    if level < self.silence_threshold:
                        silence_chunks += 1
                        if silence_chunks >= chunks_for_silence and len(recorded_chunks) > 2:
                            break
                    else:
                        silence_chunks = 0

                except queue.Empty:
                    break

        self.is_recording = False

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        if recorded_chunks:
            return np.concatenate(recorded_chunks).flatten()
        return np.array([])

    def transcribe(self, audio_data: np.ndarray = None) -> str:
        """
        Transcribe audio to text using SpeechRecognition

        Args:
            audio_data: Audio as numpy array (optional, uses mic if None)

        Returns:
            Transcribed text
        """
        if not HAS_SPEECH_RECOGNITION or self.recognizer is None:
            return ""

        try:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)

            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    return text
                except:
                    return ""

        except sr.WaitTimeoutError:
            return ""
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def listen_once(self) -> str:
        """
        Listen for speech once and return transcription

        Returns:
            Transcribed text from user's speech
        """
        text = self.transcribe()
        if text:
            print(f"Heard: {text}")
        return text

    def wait_for_wake_word(self, callback: Optional[Callable] = None) -> bool:
        """
        Continuously listen for wake word "Arthur"

        Args:
            callback: Optional function to call when wake word detected

        Returns:
            True when wake word is detected
        """
        print(f"Waiting for wake word: '{self.WAKE_WORD}'...")
        self.is_listening = True

        while self.is_listening:
            text = self.listen_once()
            if text and self.WAKE_WORD in text.lower():
                print("Wake word detected!")
                if callback:
                    callback()
                return True

        return False

    def listen_with_wake_word(self) -> Optional[str]:
        """
        Listen for wake word, then capture the full command

        Returns:
            The command after wake word, or None if not detected
        """
        text = self.listen_once()

        if text:
            lower_text = text.lower()
            if self.WAKE_WORD in lower_text:
                wake_idx = lower_text.find(self.WAKE_WORD)
                command = text[wake_idx + len(self.WAKE_WORD):].strip()
                command = command.lstrip(',').lstrip('.').strip()

                if command:
                    return command
                return ""

        return None

    def stop_listening(self):
        """Stop the listening loop"""
        self.is_listening = False
        self.is_recording = False

    def calibrate_silence_threshold(self, duration: float = 2.0):
        """
        Calibrate silence threshold based on ambient noise

        Args:
            duration: How long to sample ambient noise
        """
        if HAS_SPEECH_RECOGNITION and self.microphone:
            print("Calibrating microphone... Please remain quiet.")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            print(f"Energy threshold set to: {self.recognizer.energy_threshold}")
