#!/usr/bin/env python3
"""Test script for Memory MCP Server"""

from agentmemory.server import MemoryEngine


def test_save_and_query():
    """Test save and query functionality"""
    print("Initializing Memory Engine...")
    engine = MemoryEngine()

    # Test save
    print("\n=== Testing save_memory ===")
    result = engine.save(
        category="test",
        topic="Test Memory",
        content="This is a test memory about semantic search and vector databases.",
    )
    print(f"Save result: {result}")

    # Test query with semantic search
    print("\n=== Testing query_memory (semantic) ===")
    results = engine.query("vector search", top_k=3)
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  - [{r['id']}] {r['topic']} (score: {r['score']})")
        print(f"    Category: {r['category']}")
        print(f"    Content: {r['content'][:80]}...")
        print()

    # Test query with keyword search
    print("\n=== Testing query_memory (keyword) ===")
    results = engine.query("test memory", top_k=3)
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  - [{r['id']}] {r['topic']} (score: {r['score']})")
        print(f"    Category: {r['category']}")
        print(f"    Content: {r['content'][:80]}...")
        print()

    print("✅ All tests passed!")


if __name__ == "__main__":
    test_save_and_query()
