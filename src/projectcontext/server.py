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
import json
from typing import Any
from mcp.server.fastmcp import FastMCP
from projectcontext.memory import MemoryEngine
from projectcontext.agenda import AgendaEngine

# Initialize FastMCP server
mcp = FastMCP("MemoryEngine")

# Initialize the engines once at server startup
memory_engine = MemoryEngine()
agenda_engine = AgendaEngine()


# --- MCP Resources ---


@mcp.resource("projectcontext://usage-guidelines")
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


@mcp.resource("projectcontext://schemas/{tool}")
async def get_tool_schema(tool: str) -> str:
    """Get the JSON schema for a specific tool.

    Args:
        tool: The name of the tool to get the schema for.

    Returns:
        The tool's input schema as a JSON string.
    """
    tools = await mcp.list_tools()
    for t in tools:
        if t.name == tool:
            return json.dumps(t.inputSchema, indent=2)
    raise ValueError(f"Tool not found: {tool}")


# --- MCP Tools ---


@mcp.tool()
def save_memory(category: str, topic: str, content: str) -> dict[str, Any]:
    """Save a memory to the long-term storage.

    Args:
        category: The category of the memory (e.g., "architecture", "preference", "fix")
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


# --- MCP Prompts ---


@mcp.prompt()
def setup_project_context() -> str:
    """Template for initializing a new project with technical stack, goals, and conventions."""
    return (
        "I need to set up the context for a new project.\n\n"
        "First, please use `query_memory` to check if any context already exists for this project to avoid duplicates.\n"
        "If not, use `save_memory` to record the following sections using standard categories:\n"
        "1. Technical Stack (Category: 'architecture', Topic: 'Tech Stack')\n"
        "2. Project Goals (Category: 'context', Topic: 'Goals')\n"
        "3. Coding Conventions (Category: 'architecture', Topic: 'Conventions')\n"
        "\n"
        "For each entry, ensure the content explains the 'why' behind choices and includes specific technical details as per established best practices."
    )


@mcp.prompt()
def plan_feature_implementation() -> str:
    """Guides the model to break down a feature into a structured agenda with acceptance criteria."""
    return (
        "I want to implement a new feature. Please follow this structured workflow:\n"
        "1. **Search**: Use `query_memory` to find related architecture patterns, project constraints, or similar feature specs.\n"
        "2. **Analyze**: Review the search results and cross-reference with the current codebase to ensure information is up-to-date.\n"
        "3. **Plan**: Create a detailed plan using `create_agenda`.\n"
        "   - Include relevant memory IDs in the agenda description for context linkage.\n"
        "   - Every task must have a specific `acceptance_guard` (Definition of Done).\n"
        "4. **Execute**: Break the feature into actionable tasks, marking non-critical steps as `is_optional`."
    )


@mcp.prompt()
def summarize_and_remember(context: str) -> str:
    """Summarize a conversation or technical discussion and save it to memory.

    Args:
        context: The text or conversation history to summarize.
    """
    return (
        f"Please analyze the following context and extract key decisions, preferences, or architectural details:\n\n"
        f"{context}\n\n"
        "Then, for each key point identified:\n"
        "1. **Avoid Duplicates**: Use `query_memory` to see if a memory on this topic already exists.\n"
        "2. **Categorize**: Use standard categories (`architecture`, `fix`, `feature`, `context`, `keepsake`).\n"
        "3. **Store**: \n"
        "   - If it's a new insight, use `save_memory` with a descriptive topic (3-10 words).\n"
        "   - If it updates existing info, use `update_memory` with the existing ID to prevent hallucinations and maintain a single source of truth.\n"
        "4. **Detail**: Ensure the content explains the 'why' and includes technical specifics."
    )


@mcp.prompt()
def debug_with_history(bug_description: str) -> str:
    """Workflow for debugging issues using past bug fix memories and system context.

    Args:
        bug_description: Description of the current issue.
    """
    return (
        f"I am encountering the following issue:\n\n{bug_description}\n\n"
        "Please help me debug this by following these steps:\n"
        "1. **Search History**: Use `query_memory` to search for similar issues in the `fix` category.\n"
        "2. **Check Context**: Search for relevant `architecture` or `context` memories that might explain the system's behavior.\n"
        "3. **Verify**: Cross-reference memories with the actual code. Treat memories >1 month old with caution.\n"
        "4. **Fix & Record**: After resolution, use `save_memory` (category: 'fix') to document the root cause and the fix."
    )


@mcp.prompt()
def maintain_memory_health() -> str:
    """Workflow for identifying and updating outdated or redundant memories."""
    return (
        "I want to perform memory maintenance to prevent hallucinations and redundancy:\n"
        "1. **Identify**: Use `query_memory` with terms related to the current project status.\n"
        "2. **Evaluate**: Check timestamps and relevance scores (< 0.02 are likely false positives). Verify findings against the current codebase.\n"
        "3. **Action**: \n"
        "   - **Update**: Use `update_memory` for information that has evolved.\n"
        "   - **Delete**: Use `delete_memory` for information that is no longer accurate or has been superseded.\n"
        "   - **Consolidate**: Merge overlapping memories into a single high-quality entry."
    )


def main():
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
