import tkinter as tk
from tkinter import scrolledtext
import threading
import openai
import json
import datetime
import elevenlabs

# Configuration Constants
ElevenAPIKey = "Your_Key_Here"
voice_id = "Your_VoiceID_Here"
OPENAI_API_KEY = 'Your_Key_Here'
client = openai.ChatCompletion(api_key=OPENAI_API_KEY)

# Conversation Memory File
MEMORY_FILE = 'arthur_memory.json'

# Load and save conversation memory
def load_memory():
    try:
        with open(MEMORY_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_memory(conversation_history):
    with open(MEMORY_FILE, 'w') as file:
        json.dump(conversation_history, file)

# Voice Generation using ElevenLabs
def generate_voice(text, voice_id):
    elevenlabs.set_api_key(ElevenAPIKey)
    audio = elevenlabs.generate(
        text=text,
        voice=voice_id
    )
    elevenlabs.play(audio)

# The main ArthurGUI class
class ArthurGUI:
    def __init__(self, master):
        self.master = master
        master.title("A.R.T.H.U.R. - AI Assistant")

        # Conversation area
        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=60, height=20, state=tk.DISABLED)
        self.text_area.grid(column=0, row=0, padx=10, pady=10, columnspan=2)

        # Input area
        self.input_field = tk.Entry(master, width=50)
        self.input_field.grid(column=0, row=1, padx=10, pady=10)

        # Send button
        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.grid(column=1, row=1, padx=10, pady=10)

        # Initialize conversation history
        self.conversation_history = load_memory()

        # Display past conversation on startup
        for message in self.conversation_history:
            self.update_conversation(message["role"], message["text"])

    def update_conversation(self, role, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{role}: {message}\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.yview(tk.END)  # Auto-scroll to bottom

    def send_message(self):
        user_message = self.input_field.get()
        self.input_field.delete(0, tk.END)

        if user_message:
            self.update_conversation("User", user_message)
            self.process_message(user_message)

    def process_message(self, message):
        # Handle the message in a separate thread to avoid freezing the GUI
        thread = threading.Thread(target=self.generate_response, args=(message,))
        thread.start()

    def generate_response(self, user_message):
        global conversation_history

        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "text": user_message})

        # Generate response using GPT-4
        response = client.create(
            model="gpt-4",
            messages=self.conversation_history,
            max_tokens=100,
            temperature=0
        ).choices[0].message["content"]

        # Add AI response to conversation history
        self.conversation_history.append({"role": "A.R.T.H.U.R.", "text": response})

        # Update GUI with AI response
        self.update_conversation("A.R.T.H.U.R.", response)

        # Save updated conversation history
        save_memory(self.conversation_history)

        # Generate and play voice response
        generate_voice(response, voice_id)

# Main loop to start the GUI
if __name__ == "__main__":
    root = tk.Tk()
    arthur_gui = ArthurGUI(root)
    root.mainloop()
