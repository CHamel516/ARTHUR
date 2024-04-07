import os
import sounddevice as sd
import numpy as np
import struct
import math
import pyaudio
import requests
import openai
from openai import OpenAI
import tempfile
import datetime
import time
import elevenlabs
from google.cloud import speech_v1p1beta1 as speech
from pydub import AudioSegment
from pydub.playback import play

# Configuration Constants
GOOGLE_CREDENTIALS = "Your_Directory_Here"
LANGUAGE_CODE = "en-US"
ElevenAPIKey = "Your_Key_Here"
voice_id = "Your_VoiceID_Here"
OPENAI_API_KEY = 'Your_Key_Here'
client = OpenAI(api_key=OPENAI_API_KEY)
f_name_directory = r'Your_Directory_Here'

Threshold = 10

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # Increased the sample rate for better audio quality
swidth = 2

TIMEOUT_LENGTH = 1

# Function for Speech Recognition
class Recorder:
    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=chunk)
        self.rec = []  # Initialize the recording buffer
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS

    def record(self):
        print('Noise detected, recording beginning')
        self.rec = []  # Reset the recording buffer
        current = time.time()
        end = time.time() + TIMEOUT_LENGTH

        while current <= end:
            data = self.stream.read(chunk)
            if self.rms(data) >= Threshold:
                end = time.time() + TIMEOUT_LENGTH

            current = time.time()
            self.rec.append(data)  # Append audio data to the buffer

    def transcribe(self):
        client = speech.SpeechClient()
        audio_data = b''.join(self.rec)  # Combine all recorded audio data
        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            enable_automatic_punctuation=True,
            audio_channel_count=CHANNELS,
            sample_rate_hertz=RATE,
            language_code=LANGUAGE_CODE
        )
        cloud_response = client.recognize(request={"config": config, "audio": audio})

        if cloud_response.results:
            return cloud_response.results[0].alternatives[0].transcript
        else:
            return ""

    def listen(self):
        print('Listening beginning')
        counter = 1
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            if rms_val > Threshold:
                self.record()  # Start recording into the buffer
                print('Done with recording', counter)
                counter += 1
                transcript = self.transcribe()
                if transcript:
                    return transcript  # Return the transcribed text

if __name__ == '__main__':
    # Main Chat Loop
    openai.api_key = OPENAI_API_KEY

    print("You are now in a conversation with A.R.T.H.U.R. (AI).")
    print("Speak into the microphone. Press Ctrl+C to exit.\n")

    language = 'en'
    
    # Defining the conversation
    conversation = False
    
    conversation_history = []

    # Define temp_audio_file outside the if block
    temp_audio_file = None

    while True:
        try:
            a = Recorder()
            user_input = a.listen()
            if 'arthur' in user_input.lower():
                conversation = True
            if conversation:
                if 'goodbye' in user_input.lower():
                    response = "Hope you have a great day. Goodbye"
                    conversation_history.append({"role": "AI", "text": response})
                    content_history.append({
                        "text": response,
                        "source": "AI",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    print('==========A.R.T.H.U.R.:==========')
                    print(response)
                    print('====================')

                    # Use ElevenLabs API to generate the audio response
                    audio = elevenlabs.generate(
                    text= response,
                    voice=voice_id
                    )
                
                    # Play the audio response using elevanlabs
                    elevenlabs.play(audio)

                    conversation = False

                # Implement a command to retrieve content history
                elif user_input.lower() == "show history":
                    for entry in content_history:
                        print(f"{entry['timestamp']} - {entry['source']}: {entry['text']}")
                    break
                elif user_input:
                    # Print user input (transcript)
                    print("User:", user_input)

                    # Add user input to the conversation history
                    conversation_history.append({"role": "user", "text": user_input})

                    # A.R.T.H.U.R.'s response using GPT-4
                    response = client.chat.completions.create(
                        model ="gpt-4",
                        prompt=user_input,
                        max_tokens= 100,
                        temperature= 0
                    ).choices[0].text.strip()

                    # Update content history with relevant information
                    content_history.append({
                        "text": response,
                        "source": "AI",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                    print('==========A.R.T.H.U.R.:==========')
                    print(response)
                    print('====================')

                    # Use ElevenLabs API to generate the audio response
                    elevenlabs.set_api_key(ElevenAPIKey)
                    audio = elevenlabs.generate(
                    text= response,
                    voice=voice_id
                    )
                
                    # Play the audio response using elevanlabs
                    elevenlabs.play(audio)
                    
                user_input = None
                response = None
                print('Reset\n')

        except KeyboardInterrupt:
            break

print("Conversation Ended.")    
