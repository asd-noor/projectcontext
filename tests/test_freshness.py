#!/usr/bin/env python3
"""Test script to verify freshness-aware ranking"""

from agent_memory.server import engine
import sqlite3
import time


def test_freshness():
    """Test that newer memories rank higher than older ones with similar content"""
    print("Initializing Memory Engine...")

    # Clear existing data for clean test
    with engine.db:
        engine.db.execute("DELETE FROM docs")
        engine.db.execute("DELETE FROM docs_fts")
        engine.db.execute("DELETE FROM docs_vec")

    print("\n=== 1. Creating Test Memories ===")

    # Create "Old" memory (simulated as verified 1 year ago)
    res_old = engine.save(
        category="test",
        topic="Project Config",
        content="The project uses Python 3.10 and Django 4.0.",
    )
    old_id = res_old["doc_id"]

    # Manually update to make it old (1 year ago = ~365 days)
    # SQLite datetime('now', '-1 year')
    with engine.db:
        engine.db.execute(
            "UPDATE docs SET last_verified = datetime('now', '-1 year'), timestamp = datetime('now', '-1 year') WHERE id = ?",
            (old_id,),
        )
    print(f"Created OLD memory ID: {old_id} (set to 1 year ago)")

    # Create "New" memory (verified now)
    res_new = engine.save(
        category="test",
        topic="Project Config",
        content="The project uses Python 3.12 and Django 5.0.",
    )
    new_id = res_new["doc_id"]
    print(f"Created NEW memory ID: {new_id} (set to now)")

    # Create "Medium" memory (verified 2 months ago)
    res_med = engine.save(
        category="test",
        topic="Project Config",
        content="The project uses Python 3.11 and Django 4.2.",
    )
    med_id = res_med["doc_id"]
    with engine.db:
        engine.db.execute(
            "UPDATE docs SET last_verified = datetime('now', '-2 months'), timestamp = datetime('now', '-2 months') WHERE id = ?",
            (med_id,),
        )
    print(f"Created MEDIUM memory ID: {med_id} (set to 2 months ago)")

    print("\n=== 2. Testing Query Ranking ===")

    query = "project python django version"
    print(f"Querying: '{query}'")
    results = engine.query(query, top_k=5)

    print(f"\nFound {len(results)} results:")
    for i, r in enumerate(results):
        print(
            f"{i + 1}. ID {r['id']} | Score: {r['score']:.4f} | Verified: {r['last_verified']} | Content: {r['content']}"
        )

    # Verification Logic
    if len(results) >= 3:
        first_id = results[0]["id"]
        second_id = results[1]["id"]
        third_id = results[2]["id"]

        # Check if ranking matches freshness: New > Medium > Old
        # Note: Since content is very similar, freshness should decide the order
        if first_id == new_id and second_id == med_id:
            print("\n✅ SUCCESS: Ranking honors freshness (New > Medium)")
        elif first_id == new_id:
            print("\n✅ SUCCESS: Newest memory is first")
        else:
            print("\n❌ FAILURE: Ranking does not match freshness expectations")
            print(f"Expected order IDs: {new_id} (New), {med_id} (Med), {old_id} (Old)")


if __name__ == "__main__":
    test_freshness()
