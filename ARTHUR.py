import os
import io
import sounddevice as sd
import numpy as np
import pandas as pd
from gtts import gTTS 
import openai
from google.cloud import speech_v1p1beta1 as speech

# Configuration Constants
GOOGLE_CREDENTIALS = "/home/cjh/Documents/AudioTest/just-stock-395413-77035667209a.json"
LANGUAGE_CODE = "en-US"
OPENAI_API_KEY = 'YOUR_API_KEY'

# Function for Speech Recognition
def recognize_speech(credentials_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    
    # Record audio from microphone
    print("Listening...")
    audio_data = sd.rec(int(5 * 44100), samplerate=44100, channels=2, dtype='int16')
    sd.wait()

    # Convert audio to text using Google Cloud Speech-to-Text
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_data.tobytes())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code=LANGUAGE_CODE,
    )

    cloud_response = client.recognize(request={"config": config, "audio": audio})

    if cloud_response.results:
        print(type(cloud_response.results[0].alternatives[0].transcript))
        return cloud_response.results[0].alternatives[0].transcript
    else:
        return None

# Function f  user_input = recognize_speech(GOOGLE_CREDENTIALS)or text-to-speech

# Main Chat Loop
openai.api_key = OPENAI_API_KEY

print("You are now in a conversation with A.R.T.H.U.R. (AI).")
print("Speak into the microphone. Press Ctrl+C to exit.\n")

# ... (previous code)

# ... (previous code)

while True:
    try:
        print("Recording audio...")
        user_input = recognize_speech(GOOGLE_CREDENTIALS)
        if user_input:
            # Print user input (transcript)
            print("User input:", user_input)
            
            # A.R.T.H.U.R.'s response using GPT-3
            prompt = f"User: {user_input}\nA.R.T.H.U.R.:"
            response = openai.Completion.create(
                engine="davinci",  # Specify the engine you want to use
                prompt=prompt,
                max_tokens=50,     # Limit the response length
                temperature=0.7    # Adjust the randomness of the response
            ).choices[0].text.strip()

            print("A.R.T.H.U.R.:", response)
            user_input = None
    except KeyboardInterrupt:
        break

print("Conversation ended.")
