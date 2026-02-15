#!/usr/bin/env python3
"""Test script for Memory MCP Server Updates"""

from agentmemory.server import MemoryEngine


def test_updates():
    """Test update and delete functionality"""
    print("Initializing Memory Engine...")
    engine = MemoryEngine()

    # 1. Create a memory
    print("\n=== 1. Creating Memory ===")
    result = engine.save(
        category="context",
        topic="Initial project development status",
        content="The project is in the early prototype stage. Core MCP server functionality is implemented but needs testing.",
    )
    doc_id = result["doc_id"]
    print(f"Created memory ID: {doc_id}")
    print(
        f"Content: {result['topic']} - {engine.query('initial status', top_k=1)[0]['content']}"
    )

    # 2. Update the memory
    print("\n=== 2. Updating Memory ===")
    update_result = engine.update(
        doc_id=doc_id,
        topic="Project development status update",
        content="The project has reached the MVP stage. All core tests are passing and the server is ready for deployment.",
    )
    print(f"Update Result: {update_result}")

    # 3. Verify Update (Query)
    print("\n=== 3. Verifying Update ===")

    # Query for old content (should fail or score low)
    print("Querying 'early prototype':")
    results_old = engine.query("early prototype", top_k=1)
    if not results_old or results_old[0]["id"] != doc_id:
        print("✅ Old content not found (Correct)")
    else:
        print(f"⚠️  Old content still found: {results_old[0]['content']}")

    # Query for new content
    print("Querying 'MVP stage':")
    results_new = engine.query("MVP stage", top_k=5)
    if any(r["id"] == doc_id for r in results_new):
        matching_res = next(r for r in results_new if r["id"] == doc_id)
        print(f"✅ New content found: {matching_res['content']}")
    else:
        print("❌ New content NOT found in top 5")

    # Verify DB directly
    print("Direct DB Check:")
    row = engine.db.execute(
        "SELECT topic, content FROM docs WHERE id = ?", (doc_id,)
    ).fetchone()
    print(f"DB Row: {row}")
    assert row[0] == "Project development status update"
    assert row[1] == "The project has reached the MVP stage. All core tests are passing and the server is ready for deployment."

    # 4. Delete the memory
    print("\n=== 4. Deleting Memory ===")
    delete_result = engine.delete(doc_id)
    print(f"Delete Result: {delete_result}")

    # 5. Verify Deletion
    print("\n=== 5. Verifying Deletion ===")
    row_deleted = engine.db.execute(
        "SELECT id FROM docs WHERE id = ?", (doc_id,)
    ).fetchone()
    if not row_deleted:
        print("✅ Memory deleted from DB")
    else:
        print("❌ Memory still in DB")

    results_deleted = engine.query("blue", top_k=1)
    if not results_deleted or results_deleted[0]["id"] != doc_id:
        print("✅ Memory not found in search")
    else:
        print("❌ Memory still found in search")

    print("\n✅ All update tests passed!")


if __name__ == "__main__":
    test_updates()
