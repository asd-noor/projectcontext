# Agent Memory - MCP Server for long-term memory storage
# Copyright (C) 2026  Asaduzzaman Noor
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Agenda Engine implementation."""

import sqlite3
from typing import Any, List, Optional
from .database import get_agenda_db_path


class AgendaEngine:
    """Core agenda engine for managing plans and todo lists."""

    def __init__(self):
        self.db = sqlite3.connect(get_agenda_db_path(), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite tables and FTS triggers."""
        with self.db:
            # Main tables
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS agendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    is_active INTEGER DEFAULT 1,
                    title TEXT,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agenda_id INTEGER,
                    task_order INTEGER,
                    is_optional INTEGER DEFAULT 0,
                    details TEXT,
                    acceptance_guard TEXT,
                    is_completed INTEGER DEFAULT 0,
                    FOREIGN KEY(agenda_id) REFERENCES agendas(id) ON DELETE CASCADE
                )
                """
            )

            # Clean up old task FTS if it exists
            self.db.execute("DROP TABLE IF EXISTS tasks_fts")

            # Ensure agendas_fts exists with correct schema
            fts_info = self.db.execute("PRAGMA table_info(agendas_fts)").fetchall()
            columns = [c[1] for c in fts_info]
            if "title" not in columns or not columns:
                self.db.execute("DROP TABLE IF EXISTS agendas_fts")
                self.db.execute(
                    """
                    CREATE VIRTUAL TABLE agendas_fts USING fts5(
                        title,
                        description,
                        content='agendas',
                        content_rowid='id'
                    )
                    """
                )
                # Initial population
                self.db.execute(
                    "INSERT INTO agendas_fts(rowid, title, description) SELECT id, title, description FROM agendas"
                )

            # Triggers to keep FTS in sync automatically
            self.db.execute("DROP TRIGGER IF EXISTS agendas_ai")
            self.db.execute(
                """
                CREATE TRIGGER agendas_ai AFTER INSERT ON agendas BEGIN
                    INSERT INTO agendas_fts(rowid, title, description) VALUES (new.id, new.title, new.description);
                END
                """
            )
            self.db.execute("DROP TRIGGER IF EXISTS agendas_ad")
            self.db.execute(
                """
                CREATE TRIGGER agendas_ad AFTER DELETE ON agendas BEGIN
                    INSERT INTO agendas_fts(agendas_fts, rowid, title, description) VALUES('delete', old.id, old.title, old.description);
                END
                """
            )
            self.db.execute("DROP TRIGGER IF EXISTS agendas_au")
            self.db.execute(
                """
                CREATE TRIGGER agendas_au AFTER UPDATE ON agendas BEGIN
                    INSERT INTO agendas_fts(agendas_fts, rowid, title, description) VALUES('delete', old.id, old.title, old.description);
                    INSERT INTO agendas_fts(rowid, title, description) VALUES(new.id, new.title, new.description);
                END
                """
            )

    def create_agenda(self, tasks: List[dict], title: str = "", description: str = "") -> dict[str, Any]:
        """Create a new agenda with a list of tasks."""
        with self.db:
            cur = self.db.execute(
                "INSERT INTO agendas (title, description) VALUES (?, ?)",
                (title, description)
            )
            agenda_id = cur.lastrowid

            if agenda_id is None:
                return {"status": "error", "message": "Failed to create agenda"}

            # FTS is updated via Trigger

            for i, task in enumerate(tasks):
                self.db.execute(
                    """
                    INSERT INTO tasks (agenda_id, task_order, is_optional, details, acceptance_guard)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        agenda_id,
                        i,
                        1 if task.get("is_optional") else 0,
                        task["details"],
                        task.get("acceptance_guard"),
                    ),
                )

        return {"status": "success", "agenda_id": agenda_id}

    def list_agendas(self, active_only: bool = True) -> List[dict[str, Any]]:
        """List all agendas."""
        query = "SELECT id, is_active, title, description, created_at FROM agendas"
        if active_only:
            query += " WHERE is_active = 1"

        agendas = []
        cursor = self.db.execute(query)
        for row in cursor.fetchall():
            agenda_id, is_active, title, description, created_at = row
            agendas.append(
                {
                    "id": agenda_id,
                    "is_active": bool(is_active),
                    "title": title,
                    "description": description,
                    "created_at": created_at,
                }
            )

        return agendas

    def get_agenda(self, agenda_id: int) -> dict[str, Any]:
        """Get a detailed agenda with its tasks."""
        agenda_row = self.db.execute(
            "SELECT is_active, title, description, created_at FROM agendas WHERE id = ?", (agenda_id,)
        ).fetchone()

        if not agenda_row:
            return {"status": "error", "message": f"Agenda {agenda_id} not found"}

        is_active, title, description, created_at = agenda_row

        tasks = []
        task_cursor = self.db.execute(
            "SELECT id, task_order, is_optional, details, acceptance_guard, is_completed FROM tasks WHERE agenda_id = ? ORDER BY task_order",
            (agenda_id,),
        )
        for t_row in task_cursor.fetchall():
            tasks.append(
                {
                    "id": t_row[0],
                    "order": t_row[1],
                    "is_optional": bool(t_row[2]),
                    "details": t_row[3],
                    "acceptance_guard": t_row[4],
                    "is_completed": bool(t_row[5]),
                }
            )

        return {
            "id": agenda_id,
            "is_active": bool(is_active),
            "title": title,
            "description": description,
            "created_at": created_at,
            "tasks": tasks,
        }

    def update_task(self, task_id: int, is_completed: bool) -> dict[str, Any]:
        """Update a task's completion status."""
        with self.db:
            # Get agenda_id for this task
            row = self.db.execute(
                "SELECT agenda_id FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if not row:
                return {"status": "error", "message": f"Task {task_id} not found"}

            agenda_id = row[0]

            # Check if agenda is still active
            agenda_active = self.db.execute(
                "SELECT is_active FROM agendas WHERE id = ?", (agenda_id,)
            ).fetchone()[0]
            if not agenda_active:
                return {
                    "status": "error",
                    "message": f"Agenda {agenda_id} is already completed/inactive",
                }

            # Update task
            self.db.execute(
                "UPDATE tasks SET is_completed = ? WHERE id = ?",
                (1 if is_completed else 0, task_id),
            )

            # Check if all non-optional tasks are completed
            remaining_tasks = self.db.execute(
                "SELECT COUNT(*) FROM tasks WHERE agenda_id = ? AND is_optional = 0 AND is_completed = 0",
                (agenda_id,),
            ).fetchone()[0]

            if remaining_tasks == 0:
                self.db.execute(
                    "UPDATE agendas SET is_active = 0 WHERE id = ?", (agenda_id,)
                )
                return {
                    "status": "success",
                    "message": "Task updated and agenda marked as completed",
                }

        return {"status": "success", "message": "Task updated"}

    def update_agenda(
        self,
        agenda_id: int,
        is_active: Optional[bool] = None,
        new_tasks: Optional[List[dict]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update an agenda. Add tasks only if active. Mark inactive irreversibly."""
        with self.db:
            # Check if exists
            row = self.db.execute(
                "SELECT is_active, title, description FROM agendas WHERE id = ?", (agenda_id,)
            ).fetchone()
            if not row:
                return {"status": "error", "message": f"Agenda {agenda_id} not found"}

            current_is_active = bool(row[0])
            current_title = row[1]
            current_description = row[2]

            # Update title/description
            updated_title = title if title is not None else current_title
            updated_description = description if description is not None else current_description
            
            if title is not None or description is not None:
                self.db.execute(
                    "UPDATE agendas SET title = ?, description = ? WHERE id = ?",
                    (updated_title, updated_description, agenda_id)
                )
                # FTS updated via trigger


            # Mark as inactive if requested
            if is_active is False:
                self.db.execute(
                    "UPDATE agendas SET is_active = 0 WHERE id = ?", (agenda_id,)
                )
                current_is_active = False
            elif is_active is True and not current_is_active:
                return {
                    "status": "error",
                    "message": "Agenda is already inactive and cannot be reactivated",
                }

            # Add new tasks if requested
            if new_tasks:
                if not current_is_active:
                    return {
                        "status": "error",
                        "message": "Cannot add tasks to an inactive agenda",
                    }

                # Get current max order
                max_order_row = self.db.execute(
                    "SELECT MAX(task_order) FROM tasks WHERE agenda_id = ?",
                    (agenda_id,),
                ).fetchone()
                start_order = (
                    (max_order_row[0] + 1) if max_order_row[0] is not None else 0
                )

                for i, task in enumerate(new_tasks):
                    self.db.execute(
                        """
                        INSERT INTO tasks (agenda_id, task_order, is_optional, details, acceptance_guard)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            agenda_id,
                            start_order + i,
                            1 if task.get("is_optional") else 0,
                            task["details"],
                            task.get("acceptance_guard"),
                        ),
                    )

        return {"status": "success", "message": "Agenda updated"}

    def delete_agenda(self, agenda_id: int) -> dict[str, Any]:
        """Delete an agenda and its tasks. Only allowed if inactive."""
        with self.db:
            # Check if exists and get active status
            row = self.db.execute(
                "SELECT is_active FROM agendas WHERE id = ?", (agenda_id,)
            ).fetchone()
            if not row:
                return {"status": "error", "message": f"Agenda {agenda_id} not found"}

            is_active = bool(row[0])
            if is_active:
                return {
                    "status": "error",
                    "message": f"Cannot delete active agenda {agenda_id}. Mark it as inactive first.",
                }
            
            self.db.execute("DELETE FROM agendas WHERE id = ?", (agenda_id,))
            # FTS and tasks are cleaned up via Trigger and CASCADE

        return {"status": "success", "message": f"Agenda {agenda_id} deleted"}

    def search_agendas(self, query: str, limit: int = 10) -> List[dict[str, Any]]:
        """Search agendas by title or description."""
        # Find matching agendas
        agenda_matches = self.db.execute(
            "SELECT rowid FROM agendas_fts WHERE agendas_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, limit)
        ).fetchall()
        
        results = []
        for (aid,) in agenda_matches:
             # Fetch full agenda details
             agenda = self.get_agenda(aid)
             if "status" not in agenda: # if found
                 results.append(agenda)
        
        return results
