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
        category="architecture",
        topic="Database Design",
        content="We chose PostgreSQL for its JSONB support and reliability.",
    )
    print(f"Created architecture memory ID: {result1['doc_id']}")

    result2 = engine.save(
        category="bug_fix",
        topic="Auth Issue",
        content="Fixed the authentication timeout by increasing session duration.",
    )
    print(f"Created bug_fix memory ID: {result2['doc_id']}")

    result3 = engine.save(
        category="preference",
        topic="Code Style",
        content="Team prefers single quotes for strings in JavaScript.",
    )
    print(f"Created preference memory ID: {result3['doc_id']}")

    # 2. Test category search
    print("\n=== 2. Testing Category Search ===")

    # Search for "architecture"
    print("\nSearching for 'architecture':")
    results_arch = engine.query("architecture", top_k=5)
    print(f"Found {len(results_arch)} results:")
    for r in results_arch:
        print(f"  - ID {r['id']}: [{r['category']}] {r['topic']} (score: {r['score']})")

    if any(r["id"] == result1["doc_id"] for r in results_arch):
        print("✅ Architecture memory found!")
    else:
        print("❌ Architecture memory NOT found")

    # Search for "bug_fix"
    print("\nSearching for 'bug_fix':")
    results_bug = engine.query("bug_fix", top_k=5)
    print(f"Found {len(results_bug)} results:")
    for r in results_bug:
        print(f"  - ID {r['id']}: [{r['category']}] {r['topic']} (score: {r['score']})")

    if any(r["id"] == result2["doc_id"] for r in results_bug):
        print("✅ Bug fix memory found!")
    else:
        print("❌ Bug fix memory NOT found")

    # Search for "preference"
    print("\nSearching for 'preference':")
    results_pref = engine.query("preference", top_k=5)
    print(f"Found {len(results_pref)} results:")
    for r in results_pref:
        print(f"  - ID {r['id']}: [{r['category']}] {r['topic']} (score: {r['score']})")

    if any(r["id"] == result3["doc_id"] for r in results_pref):
        print("✅ Preference memory found!")
    else:
        print("❌ Preference memory NOT found")

    # 3. Test combined search (category + content)
    print("\n=== 3. Testing Combined Search ===")
    print("\nSearching for 'architecture database':")
    results_combined = engine.query("architecture database", top_k=5)
    print(f"Found {len(results_combined)} results:")
    for r in results_combined:
        print(f"  - ID {r['id']}: [{r['category']}] {r['topic']} (score: {r['score']})")

    if results_combined and results_combined[0]["id"] == result1["doc_id"]:
        print("✅ Architecture memory ranked highest!")
    else:
        print("⚠️  Architecture memory not ranked highest")

    print("\n✅ Category search tests completed!")


if __name__ == "__main__":
    test_category_search()
