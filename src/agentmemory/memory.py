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

"""Memory Engine implementation."""

import sqlite3
import sqlite_vec
from typing import Any
from fastembed import TextEmbedding
from .database import get_memory_db_path

MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dim model


class MemoryEngine:
    """Core memory engine with persistent embedding model."""

    def __init__(self):
        # Ensure DB directory exists if not in root (no-op if file is in root)
        # os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db = sqlite3.connect(get_memory_db_path(), check_same_thread=False)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self._init_db()
        # Initialize fastembed model once at startup
        self.model = TextEmbedding(model_name=MODEL_NAME)

    def _init_db(self):
        """Initialize SQLite tables with FTS5 and vec0 extensions."""
        with self.db:
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, category TEXT, topic TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"
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

        # Fetch full data
        final_results = []

        for doc_id, base_score in candidates:
            row = self.db.execute(
                "SELECT category, topic, content, timestamp FROM docs WHERE id = ?",
                (doc_id,),
            ).fetchone()

            if row:
                category, topic, content, timestamp_str = row

                final_results.append(
                    {
                        "id": doc_id,
                        "category": category,
                        "topic": topic,
                        "content": content,
                        "timestamp": timestamp_str,
                        "score": round(base_score, 4),
                    }
                )

        return final_results[:top_k]
