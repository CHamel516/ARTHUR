"""
ARTHUR Task Management Feature
Handles to-do lists and task tracking
"""

from typing import List, Dict, Optional
from ..core.memory import Memory


class TaskManager:
    """Manages tasks and to-do items"""

    def __init__(self, memory: Memory):
        self.memory = memory

    def add_task(self, title: str, description: str = "", priority: int = 2) -> str:
        """
        Add a new task

        Args:
            title: Task title
            description: Optional description
            priority: 1 (low), 2 (medium), 3 (high)

        Returns:
            Confirmation message
        """
        task_id = self.memory.add_task(title, description, priority)
        priority_text = {1: "low", 2: "medium", 3: "high"}.get(priority, "medium")
        return f"Task added: '{title}' with {priority_text} priority."

    def view_tasks(self, include_completed: bool = False) -> str:
        """
        Get formatted list of tasks

        Returns:
            Formatted task list string
        """
        tasks = self.memory.get_tasks(include_completed)

        if not tasks:
            return "Your task list is empty. Well done, sir."

        priority_symbols = {1: "-", 2: "*", 3: "!"}
        lines = ["Here are your current tasks:"]

        for i, task in enumerate(tasks, 1):
            symbol = priority_symbols.get(task['priority'], "*")
            status = "[Done]" if task['completed'] else ""
            lines.append(f"  {i}. {symbol} {task['title']} {status}")

        return "\n".join(lines)

    def complete_task(self, identifier: str) -> str:
        """
        Mark a task as complete by number or partial name match

        Args:
            identifier: Task number or partial name

        Returns:
            Confirmation message
        """
        tasks = self.memory.get_tasks()

        if identifier.isdigit():
            idx = int(identifier) - 1
            if 0 <= idx < len(tasks):
                task = tasks[idx]
                self.memory.complete_task(task['id'])
                return f"Excellent. Task '{task['title']}' marked as complete."
            return "I couldn't find a task with that number."

        for task in tasks:
            if identifier.lower() in task['title'].lower():
                self.memory.complete_task(task['id'])
                return f"Task '{task['title']}' marked as complete."

        return f"I couldn't find a task matching '{identifier}'."

    def remove_task(self, identifier: str) -> str:
        """
        Remove a task by number or partial name match

        Args:
            identifier: Task number or partial name

        Returns:
            Confirmation message
        """
        tasks = self.memory.get_tasks(include_completed=True)

        if identifier.isdigit():
            idx = int(identifier) - 1
            if 0 <= idx < len(tasks):
                task = tasks[idx]
                self.memory.delete_task(task['id'])
                return f"Task '{task['title']}' has been removed."
            return "I couldn't find a task with that number."

        for task in tasks:
            if identifier.lower() in task['title'].lower():
                self.memory.delete_task(task['id'])
                return f"Task '{task['title']}' has been removed."

        return f"I couldn't find a task matching '{identifier}'."

    def get_task_count(self) -> Dict:
        """Get task counts"""
        all_tasks = self.memory.get_tasks(include_completed=True)
        pending = sum(1 for t in all_tasks if not t['completed'])
        completed = sum(1 for t in all_tasks if t['completed'])
        high_priority = sum(1 for t in all_tasks if not t['completed'] and t['priority'] == 3)

        return {
            'pending': pending,
            'completed': completed,
            'high_priority': high_priority
        }

    def get_summary(self) -> str:
        """Get a quick task summary"""
        counts = self.get_task_count()

        if counts['pending'] == 0:
            return "You have no pending tasks."

        summary = f"You have {counts['pending']} pending task"
        if counts['pending'] != 1:
            summary += "s"

        if counts['high_priority'] > 0:
            summary += f", {counts['high_priority']} of which "
            summary += "is" if counts['high_priority'] == 1 else "are"
            summary += " high priority"

        return summary + "."
