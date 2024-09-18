import os
import struct
import math
import pyaudio
import openai
import datetime
import elevenlabs
import requests
import schedule
import time
from threading import Thread
from google.cloud import speech_v1p1beta1 as speech

# Configuration Constants
GOOGLE_CREDENTIALS = "Your_Directory_Here"
LANGUAGE_CODE = "en-US"
ElevenAPIKey = "Your_Key_Here"
voice_id = "Your_VoiceID_Here"
OPENAI_API_KEY = 'Your_Key_Here'
OPENWEATHER_API_KEY = 'Your_OpenWeather_API_Key'
client = openai.ChatCompletion(api_key=OPENAI_API_KEY)

Threshold = 10
SHORT_NORMALIZE = (1.0 / 32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # Increased sample rate for better audio quality
swidth = 2
TIMEOUT_LENGTH = 1

# Conversation states
class ConversationState:
    IDLE = 0
    ACTIVE = 1

conversation_state = ConversationState.IDLE

# Utility function to manage conversation history
conversation_history = []
content_history = []

def update_history(role, text):
    conversation_history.append({
        "role": role,
        "text": text,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# Voice Generation using ElevenLabs
def generate_voice(text, voice_id):
    elevenlabs.set_api_key(ElevenAPIKey)
    audio = elevenlabs.generate(
        text=text,
        voice=voice_id
    )
    elevenlabs.play(audio)

# Task Management - Simple To-Do List
tasks = []

def add_task(task):
    tasks.append(task)
    return f"Task '{task}' added to the list."

def view_tasks():
    if tasks:
        return "\n".join([f"{i + 1}. {task}" for i, task in enumerate(tasks)])
    else:
        return "Your task list is empty."

def remove_task(index):
    if 0 <= index < len(tasks):
        task = tasks.pop(index)
        return f"Task '{task}' removed from the list."
    else:
        return "Invalid task number."

# Weather Updates using OpenWeatherMap API
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        return f"The weather in {city} is currently {weather} with a temperature of {temperature}°C."
    else:
        return "Sorry, I couldn't retrieve the weather information."

# Reminder/Scheduling Feature
reminders = []

def add_reminder(task, reminder_time):
    schedule.every().day.at(reminder_time).do(execute_reminder, task)
    reminders.append({"task": task, "time": reminder_time})
    return f"Reminder set for '{task}' at {reminder_time}."

def execute_reminder(task):
    print(f"Reminder: {task}")
    generate_voice(f"Reminder: {task}", voice_id)

def view_reminders():
    if reminders:
        return "\n".join([f"{i + 1}. {reminder['task']} at {reminder['time']}" for i, reminder in enumerate(reminders)])
    else:
        return "You have no reminders set."

# Thread for running scheduled reminders
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler in a separate thread
scheduler_thread = Thread(target=run_scheduler)
scheduler_thread.start()

# Function for Speech Recognition and Audio Processing
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
        while True:
            input = self.stream.read(chunk)
            if self.rms(input) > Threshold:
                self.record()  # Start recording into the buffer
                transcript = self.transcribe()
                if transcript:
                    return transcript  # Return the transcribed text

# Command Handling
def handle_command(user_input):
    global conversation_state

    if 'goodbye' in user_input.lower():
        response = "Hope you have a great day. Goodbye"
        update_history("AI", response)
        generate_voice(response, voice_id)
        conversation_state = ConversationState.IDLE
        return

    elif 'add task' in user_input.lower():
        task = user_input.replace("add task", "").strip()
        response = add_task(task)
        update_history("AI", response)

    elif 'view tasks' in user_input.lower():
        response = view_tasks()
        update_history("AI", response)

    elif 'remove task' in user_input.lower():
        try:
            index = int(user_input.replace("remove task", "").strip()) - 1
            response = remove_task(index)
        except ValueError:
            response = "Please specify a valid task number."
        update_history("AI", response)

    elif 'weather' in user_input.lower():
        city = user_input.replace("weather in", "").strip()
        response = get_weather(city)
        update_history("AI", response)

    elif 'set reminder' in user_input.lower():
        try:
            parts = user_input.split("at")
            task = parts[0].replace("set reminder", "").strip()
            reminder_time = parts[1].strip()
            response = add_reminder(task, reminder_time)
        except IndexError:
            response = "Please specify a valid time for the reminder."
        update_history("AI", response)

    elif 'view reminders' in user_input.lower():
        response = view_reminders()
        update_history("AI", response)

    else:
        # Interact with GPT-4 for non-task related responses
        update_history("user", user_input)
        response = client.create(
            model="gpt-4",
            messages=conversation_history,
            max_tokens=100,
            temperature=0
        ).choices[0].message["content"]
        update_history("AI", response)

    generate_voice(response, voice_id)
    print(f"A.R.T.H.U.R.: {response}")

# Main Loop
if __name__ == '__main__':
    print("You are now in a conversation with A.R.T.H.U.R. (AI).")
    print("Speak into the microphone. Press Ctrl+C to exit.\n")

    try:
        recorder = Recorder()
        while True:
            user_input = recorder.listen()
            if 'arthur' in user_input.lower():
                conversation_state = ConversationState.ACTIVE

            if conversation_state == ConversationState.ACTIVE:
                handle_command(user_input)

    except KeyboardInterrupt:
        print("Conversation Ended.")