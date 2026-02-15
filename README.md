# Memory Engine MCP Server

A high-performance MCP (Model Context Protocol) server providing long-term memory storage with semantic and keyword search capabilities.

## Features

- **Fast Semantic Search**: Uses `fastembed` with `BAAI/bge-small-en-v1.5` for fast startup and low memory usage
- **Hybrid Search**: Combines keyword (FTS5) and vector search using Reciprocal Rank Fusion (RRF)
- **Agenda Engine**: Task management with full-text search for plans and todo lists
- **Persistent Storage**: SQLite-based storage with `sqlite-vec` extension
- **Sub-200ms Queries**: Keep embedding model in memory for fast response times
- **MCP Native**: Exposes `save_memory` and `query_memory` as native MCP tools

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd agentmemory

# Install dependencies with uv
uv sync

# Or install globally
uv pip install -e .
```

## Usage

### Running the Server

```bash
# Run directly
agentmemory

# Or with uv
uv run agentmemory
```

### MCP Configuration

Add to your MCP client configuration (e.g., `mcp.json`):

```json
{
  "mcpServers": {
    "memory": {
      "command": "uv",
      "args": ["run", "agentmemory"],
      "cwd": "/path/to/agentmemory"
    }
  }
}
```

Or using the installed script:

```json
{
  "mcpServers": {
    "memory": {
      "command": "agentmemory"
    }
  }
}
```

## MCP Tools

### `save_memory`

Save a memory to long-term storage.

**Arguments:**
- `category` (string): Category of the memory (e.g., "architecture", "preference", "bug_fix")
- `topic` (string): Short descriptive title
- `content` (string): Detailed memory/decision text

**Returns:**
```json
{
  "status": "success",
  "doc_id": 123,
  "topic": "Example Topic",
  "category": "architecture"
}
```

### `query_memory`

Query memories using semantic and keyword search.

**Arguments:**
- `query` (string): Natural language search string
- `top_k` (integer, optional): Number of results to return (default: 3)

**Returns:**
```json
[
  {
    "id": 123,
    "category": "architecture",
    "topic": "Example Topic",
    "content": "Detailed content...",
    "timestamp": "2024-02-04 13:22:00",
    "score": 0.8542
  }
]
```

### `delete_memory`

Delete a memory by ID.

**Arguments:**
- `doc_id` (integer): The ID of the memory to delete

**Returns:**
```json
{
  "status": "success",
  "message": "Memory 123 deleted"
}
```

### `update_memory`

Update a memory by ID.

**Arguments:**
- `doc_id` (integer): The ID of the memory to update
- `category` (string, optional): New category
- `topic` (string, optional): New topic
- `content` (string, optional): New content

**Returns:**
```json
{
  "status": "success",
  "doc_id": 123,
  "topic": "Updated Topic",
  "category": "updated_category",
      "message": "Memory updated"
  }
  ```
  
### `create_agenda`

Create a new agenda (plan/todo list).

**Arguments:**
- `tasks` (list): List of task dicts (e.g. `[{ "details": "Task 1", "is_optional": false }]`)
- `title` (string, optional): Agenda title
- `description` (string, optional): Agenda description

**Returns:**
```json
{
  "status": "success",
  "agenda_id": 1
}
```

### `list_agendas`

List all agendas.

**Arguments:**
- `active_only` (boolean, optional): If True, only show active agendas (default: True)

**Returns:**
```json
[
  {
    "id": 1,
    "is_active": true,
    "title": "My Plan",
    "description": "...",
    "created_at": "..."
  }
]
```

### `get_agenda`

Get detailed information about an agenda, including its tasks.

**Arguments:**
- `agenda_id` (integer): The ID of the agenda

**Returns:**
```json
{
  "id": 1,
  "tasks": [...]
}
```

### `search_agendas`

Search agendas by title or description.

**Arguments:**
- `query` (string): Search query
- `limit` (integer, optional): Max results (default: 10)

**Returns:**
```json
[
  {
    "id": 1,
    "title": "Matching Agenda",
    ...
  }
]
```

### `update_task`

Update a task's completion status.

**Arguments:**
- `task_id` (integer): The ID of the task
- `is_completed` (boolean): True if finished

**Returns:**
```json
{
  "status": "success",
  "message": "Task updated"
}
```

### `update_agenda`

Update an agenda's status, details, or add new tasks.

**Arguments:**
- `agenda_id` (integer): The ID of the agenda
- `is_active` (boolean, optional): Set to False to deactivate
- `new_tasks` (list, optional): List of new tasks to add
- `title` (string, optional): New title
- `description` (string, optional): New description

**Returns:**
```json
{
  "status": "success",
  "message": "Agenda updated"
}
```

### `delete_agenda`

Delete an agenda and its associated tasks (must be inactive).

**Arguments:**
- `agenda_id` (integer): The ID of the agenda

**Returns:**
```json
{
  "status": "success",
  "message": "Agenda 1 deleted"
}
```

  ## MCP Resources
### `memory://usage-guidelines`

Provides comprehensive usage guidelines for AI agents using the memory system.

**Access via MCP client:**
```python
content = await client.read_resource("memory://usage-guidelines")
print(content[0].text)
```

**Contains:**
- When to save memories (DO's and DON'Ts)
- How to structure memories (category, topic, content)
- How to query effectively
- Best practices and common patterns
- Search features and capabilities
- Privacy and security considerations

**Note:** AI agents can read this resource to understand how to use the memory system effectively. The guidelines help ensure memories are saved consistently and can be retrieved efficiently.

## Examples

### Saving a Technical Decision
**Agent:** "I'll record that we've decided to use SQLite for its simplicity and local persistence."
```python
save_memory(
    category="architecture",
    topic="Database Choice",
    content="We chose SQLite with sqlite-vec for local vector storage. This avoids external dependencies and keeps data within the project git root."
)
```

### Retrieving Project Context
**Agent:** "Let me check our previous decisions about the tech stack."
```python
query_memory(query="tech stack decisions")
# Returns: [Database Choice, Python version requirements, etc.]
```

## Architecture

### Technology Stack

- **Framework**: FastMCP (Python MCP library)
- **Embeddings**: fastembed (`BAAI/bge-small-en-v1.5`, 384-dim)
- **Database**: SQLite with `sqlite-vec` and `FTS5` extensions
- **Communication**: JSON-RPC over stdio

### Data Flow

1. **Save**: Content → Embedding → SQLite (docs + docs_fts + docs_vec)
2. **Query**: Query → Embedding → Parallel FTS5 + Vector Search → RRF Fusion → Ranked Results

### Database Schema

#### Memory Engine (Hybrid Search)
```sql
-- Main documents table
CREATE TABLE docs (
  id INTEGER PRIMARY KEY,
  category TEXT,
  topic TEXT,
  content TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search index
CREATE VIRTUAL TABLE docs_fts USING fts5(
  category, topic, content,
  content='docs',
  content_rowid='id'
);

-- Vector search index
CREATE VIRTUAL TABLE docs_vec USING vec0(
  id INTEGER PRIMARY KEY,
  embedding float[384]
);
```

#### Agenda Engine (Task Management)
```sql
-- Main agendas table
CREATE TABLE agendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_active INTEGER DEFAULT 1,
    title TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agenda_id INTEGER,
    task_order INTEGER,
    is_optional INTEGER DEFAULT 0,
    details TEXT,
    acceptance_guard TEXT,
    is_completed INTEGER DEFAULT 0,
    FOREIGN KEY(agenda_id) REFERENCES agendas(id) ON DELETE CASCADE
);

-- Full-text search for agenda titles and descriptions
CREATE VIRTUAL TABLE agendas_fts USING fts5(
    title,
    description,
    content='agendas',
    content_rowid='id'
);
```

### Storage Location
The databases are stored in the `.ctxhub/` directory in the git root (or current working directory).
- `memory.sqlite`: Memory Engine database
- `agenda.sqlite`: Agenda Engine database

This allows the memory to travel with the project while remaining hidden from version control.

## Performance

- **First Query (Memory)**: ~500ms (model initialization + query)
- **Subsequent Queries (Memory)**: <200ms (model kept in memory)
- **Agenda Queries**: <50ms (SQLite FTS5)
- **Embedding Model Size**: ~133MB (BAAI/bge-small-en-v1.5)
- **Memory Usage**: ~200MB base + model

## Development

### Project Structure

```
agentmemory/
├── src/
│   └── agentmemory/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # MCP Server
│       ├── memory.py        # Memory Engine
│       ├── agenda.py        # Agenda Engine
│       └── database.py      # Database Utilities
├── pyproject.toml
└── .ctxhub/                 # Databases
```

### Testing

The project includes a comprehensive test suite.

```bash
# Quick start: runs main tests and offers to start server
./quickstart.sh

# Run specific tests manually
uv run python tests/test_server.py
uv run python tests/test_updates.py
```

#### MCP Inspector
You can also test the tools interactively using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run agentmemory
```

## License

GPLv3
