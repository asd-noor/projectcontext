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
        """Initialize SQLite tables for agendas and tasks."""
        with self.db:
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS agendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    is_active INTEGER DEFAULT 1,
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
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS agenda_memory_relations (
                    agenda_id INTEGER,
                    memory_id INTEGER,
                    PRIMARY KEY (agenda_id, memory_id),
                    FOREIGN KEY(agenda_id) REFERENCES agendas(id) ON DELETE CASCADE
                )
                """
            )

    def create_agenda(
        self, tasks: List[dict], memory_ids: Optional[List[int]] = None
    ) -> dict[str, Any]:
        """Create a new agenda with a list of tasks."""
        with self.db:
            cur = self.db.execute("INSERT INTO agendas DEFAULT VALUES")
            agenda_id = cur.lastrowid

            if agenda_id is None:
                return {"status": "error", "message": "Failed to create agenda"}

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

        if memory_ids:
            relations = [(agenda_id, mid) for mid in memory_ids]
            self.create_agenda_memory_relations(relations)

        return {"status": "success", "agenda_id": agenda_id}

    def create_agenda_memory_relations(
        self, relations: List[tuple[int, int]]
    ) -> dict[str, Any]:
        """Add relations between agendas and memories."""
        with self.db:
            self.db.executemany(
                "INSERT OR IGNORE INTO agenda_memory_relations (agenda_id, memory_id) VALUES (?, ?)",
                relations,
            )
        return {
            "status": "success",
            "message": f"Created {len(relations)} agenda-memory relations",
        }

    def list_agendas(self, active_only: bool = True) -> List[dict[str, Any]]:
        """List all agendas."""
        query = "SELECT id, is_active, created_at FROM agendas"
        if active_only:
            query += " WHERE is_active = 1"

        agendas = []
        cursor = self.db.execute(query)
        for row in cursor.fetchall():
            agenda_id, is_active, created_at = row
            agendas.append(
                {
                    "id": agenda_id,
                    "is_active": bool(is_active),
                    "created_at": created_at,
                }
            )

        return agendas

    def get_agenda(self, agenda_id: int) -> dict[str, Any]:
        """Get a detailed agenda with its tasks."""
        agenda_row = self.db.execute(
            "SELECT is_active, created_at FROM agendas WHERE id = ?", (agenda_id,)
        ).fetchone()

        if not agenda_row:
            return {"status": "error", "message": f"Agenda {agenda_id} not found"}

        is_active, created_at = agenda_row

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
            "created_at": created_at,
            "tasks": tasks,
        }

    def get_agenda_related_memories(self, agenda_id: int) -> List[int]:
        """Fetch memory IDs related to an agenda."""
        memory_cursor = self.db.execute(
            "SELECT memory_id FROM agenda_memory_relations WHERE agenda_id = ?",
            (agenda_id,),
        )
        return [row[0] for row in memory_cursor.fetchall()]

    def get_memory_related_agendas(self, memory_id: int) -> dict[str, List[int]]:
        """Fetch agendas related to a memory, split by active status."""
        cursor = self.db.execute(
            """
            SELECT a.id, a.is_active 
            FROM agendas a
            JOIN agenda_memory_relations r ON a.id = r.agenda_id
            WHERE r.memory_id = ?
            """,
            (memory_id,),
        )

        active = []
        past = []
        for aid, is_active in cursor.fetchall():
            if is_active:
                active.append(aid)
            else:
                past.append(aid)

        return {"active": active, "past": past}

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
    ) -> dict[str, Any]:
        """Update an agenda. Add tasks only if active. Mark inactive irreversibly."""
        with self.db:
            # Check if exists
            row = self.db.execute(
                "SELECT is_active FROM agendas WHERE id = ?", (agenda_id,)
            ).fetchone()
            if not row:
                return {"status": "error", "message": f"Agenda {agenda_id} not found"}

            current_is_active = bool(row[0])

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
            # Tasks and relations are deleted via ON DELETE CASCADE

        return {"status": "success", "message": f"Agenda {agenda_id} deleted"}
