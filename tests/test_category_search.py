#!/usr/bin/env python3
"""Test script for category search functionality"""

from agentmemory.server import MemoryEngine


def test_category_search():
    """Test that category field is searchable"""
    print("Initializing Memory Engine...")
    engine = MemoryEngine()

    # 1. Create memories with different categories
    print("\n=== 1. Creating Test Memories ===")

    result1 = engine.save(
        category="feature",
        topic="User authentication system requirements",
        content="The system must support OAuth2 with Google and GitHub providers. JWT should be used for session management.",
    )
    print(f"Created feature memory ID: {result1['doc_id']}")

    result2 = engine.save(
        category="context",
        topic="Current project technical stack overview",
        content="We are using Python 3.12, FastAPI, and SQLite with vector extensions for this project.",
    )
    print(f"Created context memory ID: {result2['doc_id']}")

    result3 = engine.save(
        category="keepsake",
        topic="User preferences for code formatting",
        content="The user prefers using Black for Python formatting with a line length of 88 characters.",
    )
    print(f"Created keepsake memory ID: {result3['doc_id']}")

    # 2. Test category search
    print("\n=== 2. Testing Category Search ===")

    # Search for "feature"
    print("\nSearching for 'feature':")
    results_feat = engine.query("feature", top_k=10)
    print(f"Found {len(results_feat)} results.")

    if any(r["id"] == result1["doc_id"] for r in results_feat):
        print("✅ Feature memory found!")
    else:
        print("❌ Feature memory NOT found")

    # Search for "context"
    print("\nSearching for 'context':")
    results_ctx = engine.query("context", top_k=10)
    print(f"Found {len(results_ctx)} results.")

    if any(r["id"] == result2["doc_id"] for r in results_ctx):
        print("✅ Context memory found!")
    else:
        print("❌ Context memory NOT found")

    # Search for "keepsake"
    print("\nSearching for 'keepsake':")
    results_keep = engine.query("keepsake", top_k=10)
    print(f"Found {len(results_keep)} results.")

    if any(r["id"] == result3["doc_id"] for r in results_keep):
        print("✅ Keepsake memory found!")
    else:
        print("❌ Keepsake memory NOT found")

    # 3. Test combined search (category + content)
    print("\n=== 3. Testing Combined Search ===")
    print("\nSearching for 'feature authentication':")
    results_combined = engine.query("feature authentication", top_k=10)
    print(f"Found {len(results_combined)} results.")

    if any(r["id"] == result1["doc_id"] for r in results_combined):
        print("✅ Feature memory found in combined search!")
    else:
        print("⚠️  Feature memory not found in combined search")

    print("\n✅ Category search tests completed!")


if __name__ == "__main__":
    test_category_search()
