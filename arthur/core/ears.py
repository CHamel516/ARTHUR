"""
ARTHUR's Ears - Speech Recognition using faster-whisper
Handles wake word detection and speech-to-text conversion
"""

import numpy as np
import sounddevice as sd
import queue
import threading
from typing import Optional, Callable
from faster_whisper import WhisperModel


class Ears:
    """Handles all audio input and speech recognition for ARTHUR"""

    WAKE_WORD = "arthur"

    def __init__(self, model_size: str = "base.en", device: str = "auto"):
        """
        Initialize speech recognition

        Args:
            model_size: Whisper model size (tiny.en, base.en, small.en, medium.en)
                       .en models are English-only but faster
            device: "auto", "cpu", or "cuda"
        """
        self.model_size = model_size
        self.device = device
        self.model: Optional[WhisperModel] = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_recording = False

        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 0.5
        self.silence_threshold = 0.01
        self.silence_duration = 1.5
        self.max_recording_duration = 30

        self._load_model()

    def _load_model(self):
        """Load the Whisper model"""
        print(f"Loading Whisper model ({self.model_size})...")
        try:
            compute_type = "int8" if self.device == "cpu" else "float16"
            if self.device == "auto":
                compute_type = "int8"

            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type=compute_type
            )
            print("Whisper model loaded successfully")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            raise

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())

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

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            blocksize=chunk_samples,
            callback=self._audio_callback
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

    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data to text

        Args:
            audio_data: Audio as numpy array

        Returns:
            Transcribed text
        """
        if self.model is None:
            return ""

        if len(audio_data) == 0:
            return ""

        try:
            segments, _ = self.model.transcribe(
                audio_data,
                beam_size=5,
                language="en",
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                )
            )

            text = " ".join([segment.text for segment in segments]).strip()
            return text

        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def listen_once(self) -> str:
        """
        Listen for speech once and return transcription

        Returns:
            Transcribed text from user's speech
        """
        print("Listening...")
        audio_data = self.record_audio()

        if len(audio_data) > 0:
            text = self.transcribe(audio_data)
            if text:
                print(f"Heard: {text}")
            return text
        return ""

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
            audio_data = self.record_audio(max_duration=5)

            if len(audio_data) > 0:
                text = self.transcribe(audio_data).lower()

                if self.WAKE_WORD in text:
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
        audio_data = self.record_audio(max_duration=10)

        if len(audio_data) > 0:
            text = self.transcribe(audio_data).lower()

            if self.WAKE_WORD in text:
                wake_idx = text.find(self.WAKE_WORD)
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
        print("Calibrating microphone... Please remain quiet.")
        chunks = []
        chunk_samples = int(self.sample_rate * self.chunk_duration)

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            blocksize=chunk_samples
        ) as stream:
            for _ in range(int(duration / self.chunk_duration)):
                audio_chunk, _ = stream.read(chunk_samples)
                chunks.append(audio_chunk)

        if chunks:
            all_audio = np.concatenate(chunks)
            ambient_level = self._get_audio_level(all_audio)
            self.silence_threshold = ambient_level * 2
            print(f"Silence threshold set to: {self.silence_threshold:.4f}")
