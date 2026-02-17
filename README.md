# ProjectContext - MCP Server

> Improved Successor of [AgentMemory](https://github.com/asd-noor/agentmemory)

A high-performance MCP (Model Context Protocol) server providing long-term memory storage with semantic and keyword search capabilities, along with a structured agenda engine for task management.

## Features

- **Fast Semantic Search**: Uses `fastembed` with `BAAI/bge-small-en-v1.5` for fast startup and low memory usage
- **Hybrid Search**: Combines keyword (FTS5) and vector search using Reciprocal Rank Fusion (RRF)
- **Agenda Engine**: Task management with full-text search for plans and todo lists
- **MCP Prompts**: Specialized workflows for onboarding, feature planning, and memory maintenance
- **Persistent Storage**: SQLite-based storage with `sqlite-vec` extension
- **Sub-200ms Queries**: Keeps embedding model in memory for fast response times
- **MCP Native**: Exposes tools, resources, and prompts natively for AI agents

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projectcontext

# Install dependencies with uv
uv sync

# Or install globally
uv pip install -e .
```

## Usage

### Running the Server

```bash
# Run directly
projectcontext

# Or with uv
uv run projectcontext
```

### MCP Configuration

Add to your MCP client configuration (e.g., `mcp.json`):

```json
{
  "mcpServers": {
    "projectcontext": {
      "command": "uv",
      "args": ["run", "projectcontext"],
      "cwd": "/path/to/projectcontext"
    }
  }
}
```

Or using the installed script:

```json
{
  "mcpServers": {
    "projectcontext": {
      "command": "projectcontext"
    }
  }
}
```

## MCP Tools

### Memory Engine Tools
- `save_memory`: Save a memory with category, topic, and content.
- `query_memory`: Search memories using hybrid semantic/keyword search.
- `update_memory`: Modify an existing memory by ID.
- `delete_memory`: Remove a memory by ID.

### Agenda Engine Tools
- `create_agenda`: Create a new multi-step plan or todo list.
- `list_agendas`: Show all active or inactive agendas.
- `get_agenda`: Retrieve detailed task information for a specific agenda.
- `search_agendas`: Search plans by title or description.
- `update_task`: Mark tasks as completed or pending.
- `update_agenda`: Modify agenda metadata or add new tasks.
- `delete_agenda`: Remove inactive agendas.

## MCP Resources

### `projectcontext://usage-guidelines`
Provides comprehensive documentation for AI agents on how to effectively use the Memory and Agenda engines, including categorization best practices and hallucination prevention.

### `projectcontext://schemas/{tool}`
Provides the JSON schema for a specific tool. This is useful for AI agents to understand the required and optional parameters for each tool.

## MCP Prompts

ProjectContext includes built-in prompts to guide AI agents through complex workflows:

- **`setup_project_context`**: Templates for initializing a new project's tech stack, goals, and conventions.
- **`plan_feature_implementation`**: A structured workflow for searching existing context and creating a multi-step agenda for new features.
- **`summarize_and_remember`**: Distills conversation history into structured memories while avoiding duplicates.
- **`debug_with_history`**: A troubleshooting workflow that leverages past `bug_fix` memories and system context.
- **`maintain_memory_health`**: A proactive maintenance workflow for identifying and cleaning up outdated or redundant information.

## Architecture

### Technology Stack
- **Framework**: FastMCP (Python MCP library)
- **Embeddings**: fastembed (`BAAI/bge-small-en-v1.5`, 384-dim)
- **Database**: SQLite with `sqlite-vec` and `FTS5` extensions
- **Communication**: JSON-RPC over stdio

### Storage Location
The databases are stored in the `.ctxhub/` directory in the git root (or current working directory).
- `memory.sqlite`: Memory Engine database
- `agenda.sqlite`: Agenda Engine database

## Development

### Project Structure
```
projectcontext/
├── src/
│   └── projectcontext/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # MCP Server (Tools, Prompts, Resources)
│       ├── memory.py        # Memory Engine Logic
│       ├── agenda.py        # Agenda Engine Logic
│       └── database.py      # Database Utilities
├── pyproject.toml
└── .ctxhub/                 # Databases
```

### Testing
```bash
# Quick start: runs main tests and offers to start server
./quickstart.sh

# Run specific tests manually
uv run python tests/test_server.py
uv run python tests/test_updates.py
```

#### MCP Inspector
```bash
npx @modelcontextprotocol/inspector uv run projectcontext
```

## License
GPL-3.0-or-later
