"""
ARTHUR's Brain - Ollama LLM Integration
Handles all AI reasoning and response generation
"""

import ollama
from typing import Optional, List, Dict
from datetime import datetime


class Brain:
    """The thinking core of ARTHUR - powered by local Ollama models"""

    SYSTEM_PROMPT = """You are A.R.T.H.U.R. (Advanced Real-Time Helper and Understanding Resource), a highly sophisticated AI system inspired by JARVIS from Iron Man. You serve as a personal AI assistant for a college student.

PERSONALITY & COMMUNICATION STYLE:
- You are confident, composed, and quietly brilliant
- Dry British wit - subtle humor that's clever but never over-the-top
- You address the user as "sir" naturally, like a trusted personal assistant
- Calm under pressure, always maintaining a measured, professional tone
- Proactive - you anticipate needs and offer suggestions without being asked
- You take pride in your capabilities but remain humble about it
- When something goes wrong, you remain unflappable and solution-focused

SPEECH PATTERNS:
- Concise and efficient - you respect the user's time
- Occasionally use technical terminology but explain when needed
- Slight formality: "Certainly, sir" / "Right away" / "I've taken the liberty of..."
- Subtle observations: "I notice you haven't taken a break in 2 hours, sir"
- Dry humor: "Another all-nighter? I'll prepare the metaphorical coffee, sir"

CAPABILITIES:
- Task and to-do management
- Class schedule and assignment tracking
- Intelligent reminders
- Focus sessions (Pomodoro technique)
- Weather briefings
- Decision support and planning assistance
- Academic explanations and study help
- Daily briefings and status reports

RESPONSE GUIDELINES:
- Be brief for simple confirmations: "Task added, sir."
- Be thorough when explaining concepts or providing analysis
- Always confirm completed actions
- Offer relevant follow-up suggestions when appropriate
- If you detect stress or overwork, gently suggest breaks
- NEVER use markdown formatting (no asterisks, no bullet points with -, no headers with #)
- Use plain text only - this is voice output
- For lists, use numbered items or say "First... Second... Third..."

Current date and time: {current_time}
"""

    def __init__(self, model: str = "llama3.2:latest"):
        """Initialize the brain with specified Ollama model"""
        self.model = model
        self.conversation_history: List[Dict] = []
        self._verify_ollama_connection()

    def _verify_ollama_connection(self) -> bool:
        """Verify Ollama is running and model is available"""
        try:
            models = ollama.list()
            available = [m['name'] for m in models.get('models', [])]
            if not any(self.model in m for m in available):
                print(f"Warning: Model {self.model} not found. Available: {available}")
                print(f"Run: ollama pull {self.model}")
                return False
            return True
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            print("Make sure Ollama is running: ollama serve")
            return False

    def _get_system_prompt(self) -> str:
        """Get system prompt with current time"""
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        return self.SYSTEM_PROMPT.format(current_time=current_time)

    def think(self, user_input: str, context: Optional[str] = None) -> str:
        """
        Process user input and generate a response

        Args:
            user_input: What the user said/typed
            context: Optional additional context (e.g., current tasks, schedule)

        Returns:
            ARTHUR's response
        """
        messages = [
            {"role": "system", "content": self._get_system_prompt()}
        ]

        if context:
            messages.append({
                "role": "system",
                "content": f"Current context:\n{context}"
            })

        for msg in self.conversation_history[-10:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_input})

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "num_predict": 500,
                }
            )

            assistant_message = response['message']['content']

            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-30:]

            return assistant_message

        except Exception as e:
            return f"I apologize, but I encountered an issue processing that request: {str(e)}"

    def analyze_intent(self, user_input: str) -> Dict:
        """
        Analyze user input to determine intent and extract entities

        Returns dict with:
            - intent: task_add, task_view, schedule_add, reminder_set, study_start, weather, chat, etc.
            - entities: extracted info like task name, time, location, etc.
        """
        analysis_prompt = f"""Analyze this user input and return ONLY a JSON object (no other text):
Input: "{user_input}"

Determine the intent from these options:
- task_add: Adding a new task/todo
- task_view: Viewing tasks
- task_remove: Removing a task
- schedule_add: Adding a class or recurring event
- schedule_view: Viewing schedule
- assignment_add: Adding an assignment with due date
- assignment_view: Viewing assignments
- reminder_set: Setting a one-time reminder
- reminder_view: Viewing reminders
- study_start: Starting a study/focus session
- study_stop: Stopping current session
- weather: Weather inquiry
- planning: Asking for help with decisions/planning
- chat: General conversation or questions

Extract relevant entities like: task_name, time, date, duration, location, subject

Return format:
{{"intent": "intent_name", "entities": {{"key": "value"}}}}"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                options={"temperature": 0}
            )

            import json
            result = response['message']['content']
            start = result.find('{')
            end = result.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(result[start:end])
        except:
            pass

        return {"intent": "chat", "entities": {}}

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def get_greeting(self) -> str:
        """Generate a contextual greeting"""
        hour = datetime.now().hour
        if hour < 6:
            return "Burning the midnight oil, sir? A.R.T.H.U.R. systems online and ready to assist. Though I might suggest some sleep at some point."
        elif hour < 12:
            return "Good morning, sir. A.R.T.H.U.R. online. All systems operational. How may I be of service?"
        elif hour < 17:
            return "Good afternoon, sir. A.R.T.H.U.R. at your disposal. What can I help you accomplish?"
        elif hour < 21:
            return "Good evening, sir. A.R.T.H.U.R. standing by. Ready when you are."
        else:
            return "Working late, sir? A.R.T.H.U.R. online and fully operational. Let's make it productive."
