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

"""Memory Engine MCP Server

A long-running MCP server that provides semantic and keyword search for long-term memory storage.
"""

import os
from typing import Any
from mcp.server.fastmcp import FastMCP
from agentmemory.memory import MemoryEngine
from agentmemory.agenda import AgendaEngine

# Initialize FastMCP server
mcp = FastMCP("MemoryEngine")

# Initialize the engines once at server startup
memory_engine = MemoryEngine()
agenda_engine = AgendaEngine()


# --- MCP Resources ---


@mcp.resource("memory://usage-guidelines")
def get_usage_guidelines() -> str:
    """Memory Engine usage guidelines for AI agents.

    Provides comprehensive documentation on:
    - When to save memories (DO's and DON'Ts)
    - How to structure memories (category, topic, content)
    - How to query effectively
    - Best practices and common patterns
    - Search features and capabilities

    Returns:
        The complete usage guidelines as markdown text
    """
    guidelines_path = os.path.join(os.path.dirname(__file__), "SYSTEM_PROMPT.md")
    with open(guidelines_path, "r", encoding="utf-8") as f:
        return f.read()


# --- MCP Tools ---


@mcp.tool()
def save_memory(category: str, topic: str, content: str) -> dict[str, Any]:
    """Save a memory to the long-term storage.

    Args:
        category: The category of the memory (e.g., "architecture", "preference", "bug_fix")
        topic: A short descriptive title for the memory
        content: The detailed memory/decision text

    Returns:
        A dictionary with status, doc_id, topic, and category
    """
    return memory_engine.save(category, topic, content)


@mcp.tool()
def delete_memory(doc_id: int) -> dict[str, Any]:
    """Delete a memory by ID.

    Args:
        doc_id: The ID of the memory to delete

    Returns:
        A dictionary with status and message
    """
    return memory_engine.delete(doc_id)


@mcp.tool()
def update_memory(
    doc_id: int,
    category: str | None = None,
    topic: str | None = None,
    content: str | None = None,
) -> dict[str, Any]:
    """Update a memory by ID.

    Args:
        doc_id: The ID of the memory to update
        category: New category (optional)
        topic: New topic (optional)
        content: New content (optional)

    Returns:
        A dictionary with status and updated details
    """
    return memory_engine.update(doc_id, category, topic, content)


@mcp.tool()
def query_memory(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Query memories using semantic and keyword search.

    Args:
        query: Natural language search string
        top_k: Number of results to return (default: 3)

    Returns:
        A list of matching memories with similarity scores
    """
    return memory_engine.query(query, top_k)


# --- Agenda Tools ---


@mcp.tool()
def create_agenda(
    tasks: list[dict[str, Any]],
    title: str = "",
    description: str = "",
) -> dict[str, Any]:
    """Create a new agenda (plan/todo list).

    Args:
        tasks: List of task dicts. Each task should have:
            - details: str (required)
            - is_optional: bool (optional, default False)
            - acceptance_guard: str (optional)
        title: Optional title for the agenda
        description: Optional description for the agenda

    Returns:
        A dictionary with status and agenda_id
    """
    return agenda_engine.create_agenda(tasks, title, description)


@mcp.tool()
def list_agendas(active_only: bool = True) -> list[dict[str, Any]]:
    """List all agendas.

    Args:
        active_only: If True, only show active agendas (default: True)

    Returns:
        A list of agendas
    """
    return agenda_engine.list_agendas(active_only)


@mcp.tool()
def get_agenda(agenda_id: int) -> dict[str, Any]:
    """Get detailed information about an agenda, including its tasks.

    Args:
        agenda_id: The ID of the agenda to retrieve

    Returns:
        A dictionary with agenda details and tasks
    """
    return agenda_engine.get_agenda(agenda_id)


@mcp.tool()
def search_agendas(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search agendas by title or description.

    Args:
        query: The search query string
        limit: Maximum number of results to return (default: 10)

    Returns:
        A list of matching agendas
    """
    return agenda_engine.search_agendas(query, limit)


@mcp.tool()
def update_task(task_id: int, is_completed: bool) -> dict[str, Any]:
    """Update a task's completion status.

    If all non-optional tasks are completed, the agenda will be marked as inactive.

    Args:
        task_id: The ID of the task to update
        is_completed: True if the task is finished, False otherwise

    Returns:
        A dictionary with status and message
    """
    return agenda_engine.update_task(task_id, is_completed)


@mcp.tool()
def update_agenda(
    agenda_id: int,
    is_active: bool | None = None,
    new_tasks: list[dict[str, Any]] | None = None,
    title: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update an agenda's status, details, or add new tasks.

    Args:
        agenda_id: The ID of the agenda to update
        is_active: Set to False to deactivate the agenda (irreversible).
        new_tasks: Optional list of new task dicts to add (only if agenda is active).
        title: New title (optional)
        description: New description (optional)

    Returns:
        A dictionary with status and message
    """
    return agenda_engine.update_agenda(
        agenda_id, is_active, new_tasks, title, description
    )


@mcp.tool()
def delete_agenda(agenda_id: int) -> dict[str, Any]:
    """Delete an agenda and its associated tasks.

    Args:
        agenda_id: The ID of the agenda to delete

    Returns:
        A dictionary with status and message
    """
    return agenda_engine.delete_agenda(agenda_id)


def main():
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
