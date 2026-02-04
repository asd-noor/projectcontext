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
Uses fastembed for fast startup and low RAM usage, with Reciprocal Rank Fusion for optimal search.
"""

import sqlite3
import sqlite_vec
import os
import math
import subprocess
from datetime import datetime
from typing import Any
from mcp.server.fastmcp import FastMCP
from fastembed import TextEmbedding


# --- CONFIG ---
def get_db_path() -> str:
    """Determine the database path (git root or current directory)."""
    try:
        # Use git to find the root directory
        git_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )
        return os.path.join(git_root, ".agent-memory", "db.sqlite")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to current working directory if not a git repo or git not found
        return os.path.join(os.getcwd(), ".agent-memory", "db.sqlite")


DB_PATH = get_db_path()
MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dim model

# Initialize FastMCP server
mcp = FastMCP("MemoryEngine")


class MemoryEngine:
    """Core memory engine with persistent embedding model."""

    def __init__(self):
        # Ensure DB directory exists if not in root (no-op if file is in root)
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self._init_db()
        # Initialize fastembed model once at startup
        self.model = TextEmbedding(model_name=MODEL_NAME)

    def _init_db(self):
        """Initialize SQLite tables with FTS5 and vec0 extensions."""
        with self.db:
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, category TEXT, topic TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, last_verified DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
            self.db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(category, topic, content, content='docs', content_rowid='id')"
            )
            self.db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS docs_vec USING vec0(id INTEGER PRIMARY KEY, embedding float[384])"
            )

            # Check if FTS table exists and has correct schema
            cursor = self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='docs_fts'"
            )
            fts_exists = cursor.fetchone() is not None

            if fts_exists:
                # Check if category column exists in FTS
                cursor = self.db.execute("PRAGMA table_info(docs_fts)")
                columns = [row[1] for row in cursor.fetchall()]
                if "category" not in columns:
                    # Migration needed: rebuild FTS with category
                    self.db.execute("DROP TABLE IF EXISTS docs_fts")
                    fts_exists = False

            if not fts_exists:
                self.db.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(category, topic, content, content='docs', content_rowid='id')"
                )
                # Rebuild FTS index from existing data if docs table has data
                cursor = self.db.execute(
                    "SELECT id, category, topic, content FROM docs"
                )
                for row in cursor.fetchall():
                    doc_id, category, topic, content = row
                    self.db.execute(
                        "INSERT INTO docs_fts (rowid, category, topic, content) VALUES (?, ?, ?, ?)",
                        (doc_id, category, topic, content),
                    )

            self.db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS docs_vec USING vec0(id INTEGER PRIMARY KEY, embedding float[384])"
            )

    def save(self, category: str, topic: str, content: str) -> dict[str, Any]:
        """Save a memory with category, topic, and content."""
        # Generate embedding using fastembed
        embedding_list = list(self.model.embed([content]))
        embedding = embedding_list[0].tolist()

        with self.db:
            cur = self.db.execute(
                "INSERT INTO docs (category, topic, content) VALUES (?, ?, ?)",
                (category, topic, content),
            )
            doc_id = cur.lastrowid
            self.db.execute(
                "INSERT INTO docs_fts (rowid, category, topic, content) VALUES (?, ?, ?, ?)",
                (doc_id, category, topic, content),
            )
            self.db.execute(
                "INSERT INTO docs_vec (id, embedding) VALUES (?, ?)",
                (doc_id, sqlite_vec.serialize_float32(embedding)),
            )

        return {
            "status": "success",
            "doc_id": doc_id,
            "topic": topic,
            "category": category,
        }

    def update(
        self,
        doc_id: int,
        category: str | None = None,
        topic: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Update a memory by ID."""
        with self.db:
            # Check if exists and get current values
            row = self.db.execute(
                "SELECT category, topic, content FROM docs WHERE id = ?", (doc_id,)
            ).fetchone()
            if not row:
                return {
                    "status": "error",
                    "message": f"Memory with ID {doc_id} not found",
                }

            current_category, current_topic, current_content = row

            # Use new values or fall back to current
            new_category = category if category is not None else current_category
            new_topic = topic if topic is not None else current_topic
            new_content = content if content is not None else current_content

            # Update docs table
            self.db.execute(
                "UPDATE docs SET category = ?, topic = ?, content = ? WHERE id = ?",
                (new_category, new_topic, new_content, doc_id),
            )

            # Update FTS if topic or content changed
            if category is not None or topic is not None or content is not None:
                # FTS update is typically a DELETE + INSERT to ensure consistency
                self.db.execute("DELETE FROM docs_fts WHERE rowid = ?", (doc_id,))
                self.db.execute(
                    "INSERT INTO docs_fts (rowid, category, topic, content) VALUES (?, ?, ?, ?)",
                    (doc_id, new_category, new_topic, new_content),
                )

            # Update Vector if content changed
            if content is not None:
                embedding_list = list(self.model.embed([new_content]))
                embedding = embedding_list[0].tolist()
                self.db.execute("DELETE FROM docs_vec WHERE id = ?", (doc_id,))
                self.db.execute(
                    "INSERT INTO docs_vec (id, embedding) VALUES (?, ?)",
                    (doc_id, sqlite_vec.serialize_float32(embedding)),
                )

        return {
            "status": "success",
            "doc_id": doc_id,
            "topic": new_topic,
            "category": new_category,
            "message": "Memory updated",
        }

    def delete(self, doc_id: int) -> dict[str, Any]:
        """Delete a memory by ID."""
        with self.db:
            # Check if exists
            row = self.db.execute(
                "SELECT id FROM docs WHERE id = ?", (doc_id,)
            ).fetchone()
            if not row:
                return {
                    "status": "error",
                    "message": f"Memory with ID {doc_id} not found",
                }

            # Delete from all tables
            self.db.execute("DELETE FROM docs WHERE id = ?", (doc_id,))
            self.db.execute("DELETE FROM docs_fts WHERE rowid = ?", (doc_id,))
            self.db.execute("DELETE FROM docs_vec WHERE id = ?", (doc_id,))

        return {"status": "success", "message": f"Memory {doc_id} deleted"}

    def query(self, query_text: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Query memories using Reciprocal Rank Fusion of keyword and semantic search."""
        # Generate query embedding
        embedding_list = list(self.model.embed([query_text]))
        query_vec = embedding_list[0].tolist()

        # Keyword search (FTS5) - Fetch more candidates for re-ranking
        fts_rows = self.db.execute(
            "SELECT rowid FROM docs_fts WHERE docs_fts MATCH ? ORDER BY rank LIMIT 20",
            (query_text,),
        ).fetchall()

        # Vector search - Fetch more candidates for re-ranking
        vec_rows = self.db.execute(
            "SELECT id FROM docs_vec WHERE embedding MATCH ? AND k = 20 ORDER BY distance",
            (sqlite_vec.serialize_float32(query_vec),),
        ).fetchall()

        # Reciprocal Rank Fusion
        scores = {}
        for r, (idx,) in enumerate(fts_rows):
            scores[idx] = scores.get(idx, 0) + 1 / (r + 60)
        for r, (idx,) in enumerate(vec_rows):
            scores[idx] = scores.get(idx, 0) + 1 / (r + 60)

        # Get top candidates (2x top_k or at least 10) to apply freshness ranking
        candidate_limit = max(top_k * 2, 10)
        candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)[
            :candidate_limit
        ]

        if not candidates:
            return []

        # Fetch full data and apply freshness boost
        final_results = []
        now = datetime.now()

        for doc_id, base_score in candidates:
            row = self.db.execute(
                "SELECT category, topic, content, timestamp, last_verified FROM docs WHERE id = ?",
                (doc_id,),
            ).fetchone()

            if row:
                category, topic, content, timestamp_str, last_verified_str = row

                # Calculate freshness factor
                try:
                    # Parse timestamp (SQLite format: "YYYY-MM-DD HH:MM:SS")
                    last_verified = datetime.strptime(
                        last_verified_str, "%Y-%m-%d %H:%M:%S"
                    )
                    age_days = (now - last_verified).total_seconds() / 86400

                    # Mild decay: 1.0 - (log(age + 1) * 0.05)
                    # Example: 0 days -> 1.0, 30 days -> 0.83, 365 days -> 0.70
                    freshness_factor = max(
                        0.5, 1.0 - (math.log(max(0, age_days) + 1) * 0.05)
                    )
                except (ValueError, TypeError):
                    # Fallback if parsing fails
                    freshness_factor = 1.0

                final_score = base_score * freshness_factor

                final_results.append(
                    {
                        "id": doc_id,
                        "category": category,
                        "topic": topic,
                        "content": content,
                        "timestamp": timestamp_str,
                        "last_verified": last_verified_str,
                        "score": round(final_score, 4),
                        "_base_score": round(base_score, 4),  # Debug info
                    }
                )

        # Re-sort by final adjusted score
        final_results.sort(key=lambda x: x["score"], reverse=True)

        return final_results[:top_k]


# Initialize the engine once at server startup
engine = MemoryEngine()


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
    try:
        with open(guidelines_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback if file is not found
        return """# Memory Engine Usage Guidelines

## Quick Start

### When to Save Memories
- Architecture decisions and technical choices
- User preferences (code style, conventions)
- Bug fixes and their root causes
- Important project context

### How to Structure
- **category**: Use descriptive names like "architecture", "preference", "bug_fix"
- **topic**: Short title (3-10 words)
- **content**: Detailed information with context

### How to Query
- Use natural language: "What database are we using?"
- Search by category: "architecture decisions"
- All fields (category, topic, content) are searchable

### Best Practices
1. Query before saving to avoid duplicates
2. Update existing memories instead of creating duplicates
3. Use consistent category names
4. Make content searchable with relevant keywords
5. Delete outdated information

For complete documentation, see SYSTEM_PROMPT.md in the repository.
"""


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
    return engine.save(category, topic, content)


@mcp.tool()
def delete_memory(doc_id: int) -> dict[str, Any]:
    """Delete a memory by ID.

    Args:
        doc_id: The ID of the memory to delete

    Returns:
        A dictionary with status and message
    """
    return engine.delete(doc_id)


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
    return engine.update(doc_id, category, topic, content)


@mcp.tool()
def verify_memory(doc_id: int) -> dict[str, Any]:
    """Mark a memory as verified, updating its last_verified timestamp to now.

    Use this when you've confirmed the memory is still accurate and up-to-date.
    This helps track memory freshness and prevents hallucinations from outdated information.

    Args:
        doc_id: The ID of the memory to verify

    Returns:
        A dictionary with status and message
    """
    with engine.db:
        # Check if exists
        row = engine.db.execute(
            "SELECT id FROM docs WHERE id = ?", (doc_id,)
        ).fetchone()
        if not row:
            return {
                "status": "error",
                "message": f"Memory with ID {doc_id} not found",
            }

        # Update last_verified to current timestamp
        engine.db.execute(
            "UPDATE docs SET last_verified = CURRENT_TIMESTAMP WHERE id = ?",
            (doc_id,),
        )

    return {
        "status": "success",
        "doc_id": doc_id,
        "message": "Memory verified and timestamp updated",
    }


@mcp.tool()
def query_memory(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Query memories using semantic and keyword search.

    Args:
        query: Natural language search string
        top_k: Number of results to return (default: 3)

    Returns:
        A list of matching memories with similarity scores
    """
    return engine.query(query, top_k)


def main():
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
