"""
ARTHUR's Memory - SQLite Database and Conversation History
Handles persistent storage for all ARTHUR features
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path


class Memory:
    """Persistent memory storage for ARTHUR using SQLite"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize memory storage

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "arthur.db")

        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 2,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                location TEXT,
                days TEXT,
                start_time TEXT,
                end_time TEXT,
                semester TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course TEXT,
                due_date DATE,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                priority INTEGER DEFAULT 2,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                recurring TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                duration_minutes INTEGER,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def add_task(self, title: str, description: str = "", priority: int = 2) -> int:
        """Add a new task"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (title, description, priority) VALUES (?, ?, ?)',
            (title, description, priority)
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id

    def get_tasks(self, include_completed: bool = False) -> List[Dict]:
        """Get all tasks"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_completed:
            cursor.execute('SELECT * FROM tasks ORDER BY priority DESC, created_at DESC')
        else:
            cursor.execute('SELECT * FROM tasks WHERE completed = FALSE ORDER BY priority DESC, created_at DESC')

        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tasks SET completed = TRUE, completed_at = ? WHERE id = ?',
            (datetime.now(), task_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def add_class(self, title: str, days: str, start_time: str,
                  end_time: str, location: str = "", semester: str = "") -> int:
        """Add a class to the schedule"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO schedule (title, days, start_time, end_time, location, semester)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (title, days, start_time, end_time, location, semester)
        )
        class_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return class_id

    def get_schedule(self, day: Optional[str] = None) -> List[Dict]:
        """Get class schedule, optionally filtered by day"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if day:
            cursor.execute(
                'SELECT * FROM schedule WHERE days LIKE ? ORDER BY start_time',
                (f'%{day}%',)
            )
        else:
            cursor.execute('SELECT * FROM schedule ORDER BY start_time')

        schedule = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return schedule

    def get_next_class(self) -> Optional[Dict]:
        """Get the next upcoming class"""
        now = datetime.now()
        day_map = {0: 'M', 1: 'T', 2: 'W', 3: 'R', 4: 'F', 5: 'S', 6: 'U'}
        current_day = day_map[now.weekday()]
        current_time = now.strftime('%H:%M')

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''SELECT * FROM schedule
               WHERE days LIKE ? AND start_time > ?
               ORDER BY start_time LIMIT 1''',
            (f'%{current_day}%', current_time)
        )
        result = cursor.fetchone()

        if not result:
            next_day_idx = (now.weekday() + 1) % 7
            next_day = day_map[next_day_idx]
            cursor.execute(
                '''SELECT * FROM schedule
                   WHERE days LIKE ?
                   ORDER BY start_time LIMIT 1''',
                (f'%{next_day}%',)
            )
            result = cursor.fetchone()

        conn.close()
        return dict(result) if result else None

    def add_assignment(self, title: str, due_date: str, course: str = "",
                       description: str = "", priority: int = 2) -> int:
        """Add an assignment"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO assignments (title, due_date, course, description, priority)
               VALUES (?, ?, ?, ?, ?)''',
            (title, due_date, course, description, priority)
        )
        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return assignment_id

    def get_assignments(self, include_completed: bool = False) -> List[Dict]:
        """Get all assignments ordered by due date"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_completed:
            cursor.execute('SELECT * FROM assignments ORDER BY due_date ASC')
        else:
            cursor.execute('SELECT * FROM assignments WHERE completed = FALSE ORDER BY due_date ASC')

        assignments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return assignments

    def get_upcoming_assignments(self, days: int = 7) -> List[Dict]:
        """Get assignments due within specified days"""
        conn = self._get_connection()
        cursor = conn.cursor()
        future_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute(
            '''SELECT * FROM assignments
               WHERE completed = FALSE AND due_date <= ?
               ORDER BY due_date ASC''',
            (future_date,)
        )
        assignments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return assignments

    def complete_assignment(self, assignment_id: int) -> bool:
        """Mark an assignment as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE assignments SET completed = TRUE WHERE id = ?',
            (assignment_id,)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def add_reminder(self, message: str, remind_at: datetime, recurring: str = None) -> int:
        """Add a reminder"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO reminders (message, remind_at, recurring) VALUES (?, ?, ?)',
            (message, remind_at, recurring)
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reminder_id

    def get_pending_reminders(self) -> List[Dict]:
        """Get all pending reminders"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM reminders WHERE completed = FALSE ORDER BY remind_at ASC'
        )
        reminders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return reminders

    def get_due_reminders(self) -> List[Dict]:
        """Get reminders that are due now"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute(
            'SELECT * FROM reminders WHERE completed = FALSE AND remind_at <= ?',
            (now,)
        )
        reminders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return reminders

    def complete_reminder(self, reminder_id: int) -> bool:
        """Mark a reminder as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE reminders SET completed = TRUE WHERE id = ?',
            (reminder_id,)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def log_study_session(self, subject: str, duration_minutes: int,
                          started_at: datetime, ended_at: datetime, completed: bool = True) -> int:
        """Log a completed study session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO study_sessions (subject, duration_minutes, started_at, ended_at, completed)
               VALUES (?, ?, ?, ?, ?)''',
            (subject, duration_minutes, started_at, ended_at, completed)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id

    def get_study_stats(self, days: int = 7) -> Dict:
        """Get study statistics for the past N days"""
        conn = self._get_connection()
        cursor = conn.cursor()
        start_date = datetime.now() - timedelta(days=days)

        cursor.execute(
            '''SELECT SUM(duration_minutes) as total_minutes,
                      COUNT(*) as session_count,
                      AVG(duration_minutes) as avg_duration
               FROM study_sessions
               WHERE completed = TRUE AND started_at >= ?''',
            (start_date,)
        )
        result = cursor.fetchone()
        conn.close()

        return {
            'total_minutes': result['total_minutes'] or 0,
            'session_count': result['session_count'] or 0,
            'avg_duration': result['avg_duration'] or 0
        }

    def save_conversation(self, role: str, content: str):
        """Save a conversation message"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO conversations (role, content) VALUES (?, ?)',
            (role, content)
        )
        conn.commit()
        conn.close()

    def get_recent_conversations(self, limit: int = 20) -> List[Dict]:
        """Get recent conversation history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return list(reversed(conversations))

    def set_preference(self, key: str, value: str):
        """Set a user preference"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)',
            (key, value)
        )
        conn.commit()
        conn.close()

    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """Get a user preference"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result['value'] if result else default

    def get_context_summary(self) -> str:
        """Get a summary of current context for the AI"""
        tasks = self.get_tasks()
        assignments = self.get_upcoming_assignments(days=7)
        next_class = self.get_next_class()
        reminders = self.get_pending_reminders()

        context_parts = []

        if tasks:
            task_list = ", ".join([t['title'] for t in tasks[:5]])
            context_parts.append(f"Active tasks: {task_list}")

        if assignments:
            assignment_list = ", ".join([f"{a['title']} (due {a['due_date']})" for a in assignments[:3]])
            context_parts.append(f"Upcoming assignments: {assignment_list}")

        if next_class:
            context_parts.append(f"Next class: {next_class['title']} at {next_class['start_time']}")

        if reminders:
            reminder_count = len(reminders)
            context_parts.append(f"Pending reminders: {reminder_count}")

        return "\n".join(context_parts) if context_parts else "No active items."
