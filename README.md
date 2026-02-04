# Memory Engine MCP Server

A high-performance MCP (Model Context Protocol) server providing long-term memory storage with semantic and keyword search capabilities.

## Features

- **Fast Semantic Search**: Uses `fastembed` with `BAAI/bge-small-en-v1.5` for fast startup and low memory usage
- **Hybrid Search**: Combines keyword (FTS5) and vector search using Reciprocal Rank Fusion (RRF)
- **Persistent Storage**: SQLite-based storage with `sqlite-vec` extension
- **Sub-200ms Queries**: Keep embedding model in memory for fast response times
- **MCP Native**: Exposes `save_memory` and `query_memory` as native MCP tools

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd agent-memory

# Install dependencies with uv
uv sync

# Or install globally
uv pip install -e .
```

## Usage

### Running the Server

```bash
# Run directly
agent-memory

# Or with uv
uv run agent-memory
```

### MCP Configuration

Add to your MCP client configuration (e.g., `mcp.json`):

```json
{
  "mcpServers": {
    "memory": {
      "command": "uv",
      "args": ["run", "agent-memory"],
      "cwd": "/path/to/agent-memory"
    }
  }
}
```

Or using the installed script:

```json
{
  "mcpServers": {
    "memory": {
      "command": "agent-memory"
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
    "last_verified": "2024-02-04 13:22:00",
    "score": 0.8542
  }
]
```

**Note:** `last_verified` indicates when the memory was last confirmed as accurate. Use `verify_memory` to update this timestamp.

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

### `verify_memory`

Mark a memory as verified by updating its `last_verified` timestamp to now.

**Use this when:**
- You've confirmed a memory is still accurate
- You've checked information against current code
- You want to prevent hallucinations from stale data

**Arguments:**
- `doc_id` (integer): The ID of the memory to verify

**Returns:**
```json
{
  "status": "success",
  "doc_id": 123,
  "message": "Memory verified and timestamp updated"
}
```

**Note:** This helps track memory freshness. Memories with old `last_verified` timestamps should be treated with caution.

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

### Preventing Stale Data
**Agent:** "I just verified that the Python version requirement is still 3.12."
```python
verify_memory(doc_id=123)
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

```sql
-- Main documents table
CREATE TABLE docs (
  id INTEGER PRIMARY KEY,
  category TEXT,
  topic TEXT,
  content TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_verified DATETIME DEFAULT CURRENT_TIMESTAMP
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

### Storage Location
The database is stored in `.agent-memory/db.sqlite` in the git root directory (or current working directory if not in a git repo). This allows the memory to travel with the project while remaining hidden from version control.

## Performance

- **First Query**: ~500ms (model initialization + query)
- **Subsequent Queries**: <200ms (model kept in memory)
- **Embedding Model Size**: ~133MB (BAAI/bge-small-en-v1.5)
- **Memory Usage**: ~200MB base + model

## Development

### Project Structure

```
agent-memory/
├── src/
│   └── agent_memory/
│       ├── __init__.py
│       └── server.py       # MCP server implementation
├── pyproject.toml          # Project configuration
└── .agent-memory/
    └── db.sqlite           # Persistent database (in git root)
```

### Testing

The project includes a comprehensive test suite.

```bash
# Quick start: runs main tests and offers to start server
./quickstart.sh

# Run specific tests manually
uv run python tests/test_server.py
uv run python tests/test_freshness.py
uv run python tests/test_updates.py
```

#### MCP Inspector
You can also test the tools interactively using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run agent-memory
```

## License

MIT
