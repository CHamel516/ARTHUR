"""
ARTHUR Planning Assistant Feature
Helps with decision-making, planning, and organization
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..core.memory import Memory
from ..core.brain import Brain


class PlanningAssistant:
    """Helps with planning, decisions, and organization"""

    def __init__(self, memory: Memory, brain: Brain):
        """
        Initialize planning assistant

        Args:
            memory: Memory instance
            brain: Brain instance for AI-powered suggestions
        """
        self.memory = memory
        self.brain = brain

    def get_daily_briefing(self) -> str:
        """
        Generate a morning briefing of the day ahead

        Returns:
            Comprehensive daily overview
        """
        now = datetime.now()
        day_name = now.strftime('%A')

        parts = [f"Good morning, sir. Here's your briefing for {day_name}:"]

        day_map = {0: 'M', 1: 'T', 2: 'W', 3: 'R', 4: 'F', 5: 'S', 6: 'U'}
        today_abbrev = day_map[now.weekday()]
        schedule = self.memory.get_schedule(today_abbrev)

        if schedule:
            parts.append(f"\nClasses today ({len(schedule)}):")
            for cls in schedule:
                time_str = cls['start_time']
                loc = f" in {cls['location']}" if cls['location'] else ""
                parts.append(f"  - {cls['title']} at {time_str}{loc}")
        else:
            parts.append("\nNo classes scheduled for today.")

        assignments = self.memory.get_upcoming_assignments(3)
        if assignments:
            parts.append(f"\nUpcoming assignments ({len(assignments)}):")
            for a in assignments:
                parts.append(f"  - {a['title']} (due {a['due_date']})")

        tasks = self.memory.get_tasks()
        high_priority = [t for t in tasks if t['priority'] == 3]
        if high_priority:
            parts.append(f"\nHigh priority tasks ({len(high_priority)}):")
            for t in high_priority[:3]:
                parts.append(f"  - {t['title']}")
        elif tasks:
            parts.append(f"\nYou have {len(tasks)} pending task{'s' if len(tasks) != 1 else ''}.")

        reminders = self.memory.get_pending_reminders()
        today_reminders = []
        for r in reminders:
            remind_at = r['remind_at']
            if isinstance(remind_at, str):
                remind_at = datetime.fromisoformat(remind_at)
            if remind_at.date() == now.date():
                today_reminders.append(r)

        if today_reminders:
            parts.append(f"\nReminders for today ({len(today_reminders)}):")
            for r in today_reminders:
                remind_at = r['remind_at']
                if isinstance(remind_at, str):
                    remind_at = datetime.fromisoformat(remind_at)
                time_str = remind_at.strftime('%I:%M %p')
                parts.append(f"  - {r['message']} at {time_str}")

        return "\n".join(parts)

    def help_with_decision(self, decision_context: str) -> str:
        """
        Help user work through a decision

        Args:
            decision_context: Description of the decision to make

        Returns:
            AI-generated decision framework/advice
        """
        prompt = f"""The user needs help making a decision. Help them think through it systematically.

Decision: {decision_context}

Provide:
1. Key factors to consider (3-5 points)
2. Potential pros and cons of the main options
3. Questions they should ask themselves
4. A gentle recommendation if appropriate

Keep the response concise and practical. This is a college student, so consider factors like time, money, academic impact, and well-being."""

        return self.brain.think(prompt)

    def suggest_study_plan(self, subject: str = None, exam_date: str = None) -> str:
        """
        Generate a study plan suggestion

        Args:
            subject: Subject to study
            exam_date: When the exam is (optional)

        Returns:
            Study plan recommendation
        """
        context = self.memory.get_context_summary()
        stats = self.memory.get_study_stats(7)

        prompt = f"""Create a practical study plan for a college student.

Subject: {subject or 'General studies'}
Exam date: {exam_date or 'Not specified'}

Current context:
{context}

Recent study habits:
- Total study time this week: {stats['total_minutes']} minutes
- Sessions completed: {stats['session_count']}

Provide:
1. Recommended study schedule
2. Suggested techniques for this subject
3. Break recommendations
4. Tips for retention

Keep it practical and achievable. Use the Pomodoro technique as a base."""

        return self.brain.think(prompt)

    def prioritize_tasks(self) -> str:
        """
        Help prioritize current tasks and assignments

        Returns:
            Prioritization advice
        """
        tasks = self.memory.get_tasks()
        assignments = self.memory.get_upcoming_assignments(14)

        if not tasks and not assignments:
            return "You have no pending tasks or assignments. Enjoy your free time, sir."

        items = []
        for t in tasks:
            items.append(f"Task: {t['title']} (priority: {t['priority']})")
        for a in assignments:
            items.append(f"Assignment: {a['title']} (due: {a['due_date']})")

        prompt = f"""Help prioritize these items for a college student:

{chr(10).join(items)}

Consider:
- Due dates and urgency
- Importance and impact
- Dependencies between tasks
- Energy levels throughout the day

Provide a recommended order to tackle these, with brief reasoning."""

        return self.brain.think(prompt)

    def weekly_review(self) -> str:
        """
        Generate a weekly review and planning session

        Returns:
            Weekly review summary
        """
        stats = self.memory.get_study_stats(7)
        tasks = self.memory.get_tasks(include_completed=True)
        completed_tasks = [t for t in tasks if t['completed']]
        pending_tasks = [t for t in tasks if not t['completed']]
        assignments = self.memory.get_upcoming_assignments(7)

        parts = ["Weekly Review:"]

        parts.append(f"\nAccomplishments:")
        parts.append(f"  - Completed {len(completed_tasks)} task{'s' if len(completed_tasks) != 1 else ''}")
        parts.append(f"  - Studied for {stats['total_minutes']} minutes ({stats['session_count']} sessions)")

        if pending_tasks:
            parts.append(f"\nCarrying forward:")
            for t in pending_tasks[:5]:
                parts.append(f"  - {t['title']}")

        if assignments:
            parts.append(f"\nUpcoming this week:")
            for a in assignments:
                parts.append(f"  - {a['title']} (due {a['due_date']})")

        suggestions = []
        if stats['total_minutes'] < 300:
            suggestions.append("Consider increasing study time - aim for at least 5 hours per week")
        if stats['session_count'] > 0 and stats['avg_duration'] < 20:
            suggestions.append("Try longer focus sessions - 25 minutes is the sweet spot")
        if len(pending_tasks) > 10:
            suggestions.append("You have many pending tasks - consider breaking them down or delegating")

        if suggestions:
            parts.append(f"\nSuggestions for improvement:")
            for s in suggestions:
                parts.append(f"  - {s}")

        return "\n".join(parts)

    def quick_advice(self, topic: str) -> str:
        """
        Get quick advice on a topic

        Args:
            topic: What to get advice about

        Returns:
            Brief, practical advice
        """
        prompt = f"""Give brief, practical advice on: {topic}

Context: This is for a college student. Keep the response to 2-3 sentences maximum. Be direct and actionable."""

        return self.brain.think(prompt)
