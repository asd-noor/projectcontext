"""Memory Engine MCP Server

A long-running MCP server that provides semantic and keyword search for long-term memory storage.
"""

__version__ = "0.1.0"

from agentmemory.server import (
    main,
    save_memory,
    query_memory,
    create_agenda,
    list_agendas,
    get_agenda,
    update_task,
    update_agenda,
    delete_agenda,
    search_agendas,
)

__all__ = [
    "main",
    "save_memory",
    "query_memory",
    "create_agenda",
    "list_agendas",
    "get_agenda",
    "update_task",
    "update_agenda",
    "delete_agenda",
    "search_agendas",
]
