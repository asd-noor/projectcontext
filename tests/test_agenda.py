#!/usr/bin/env python3
"""Test script for Agenda functionality"""

from agentmemory.agenda import AgendaEngine
from agentmemory.memory import MemoryEngine


def test_agenda():
    print("Initializing Engines...")
    m_engine = MemoryEngine()
    a_engine = AgendaEngine()

    # 1. Create some memories to relate to
    print("\n=== 1. Creating Test Memory ===")
    m_result = m_engine.save(
        category="test", topic="Agenda Context", content="Context for agenda."
    )
    memory_id = m_result["doc_id"]
    print(f"Created memory ID: {memory_id}")

    # 2. Create an agenda
    print("\n=== 2. Creating Agenda ===")
    tasks = [
        {"description": "Task 1 (Required)", "is_optional": False},
        {
            "description": "Task 2 (Optional)",
            "is_optional": True,
            "acceptance_guard": "Must be optional",
        },
        {"description": "Task 3 (Required)", "is_optional": False},
    ]
    a_result = a_engine.create_agenda(tasks=tasks, memory_ids=[memory_id])
    agenda_id = a_result["agenda_id"]
    print(f"Created agenda ID: {agenda_id}")

    # 3. List agendas
    print("\n=== 3. Listing Agendas ===")
    agendas = a_engine.list_agendas(active_only=True)
    print(f"Active agendas: {agendas}")
    assert any(a["id"] == agenda_id for a in agendas)

    # 4. Get agenda details
    print("\n=== 4. Getting Agenda Details ===")
    details = a_engine.get_agenda(agenda_id)
    print(f"Agenda Details: {details}")
    assert len(details["tasks"]) == 3
    assert "related_memories" not in details
    
    related_memories = a_engine.get_agenda_related_memories(agenda_id)
    print(f"Related Memories: {related_memories}")
    assert memory_id in related_memories

    memory_related_agendas = a_engine.get_memory_related_agendas(memory_id)
    print(f"Memory Related Agendas: {memory_related_agendas}")
    assert agenda_id in memory_related_agendas["active"]

    # 5. Update tasks and check auto-completion
    print("\n=== 5. Updating Tasks ===")
    task1_id = details["tasks"][0]["id"]
    task2_id = details["tasks"][1]["id"]
    task3_id = details["tasks"][2]["id"]

    print(f"Completing Task 1 (Required)...")
    a_engine.update_task(task1_id, True)
    details = a_engine.get_agenda(agenda_id)
    assert details["is_active"] is True
    assert details["tasks"][0]["is_completed"] is True

    print(f"Completing Task 2 (Optional)...")
    a_engine.update_task(task2_id, True)
    details = a_engine.get_agenda(agenda_id)
    assert details["is_active"] is True

    print(f"Completing Task 3 (Required)...")
    update_res = a_engine.update_task(task3_id, True)
    print(f"Update Result: {update_res}")
    details = a_engine.get_agenda(agenda_id)
    print(f"Agenda Active: {details['is_active']}")
    assert details["is_active"] is False
    assert "marked as completed" in update_res["message"]

    # 5.1 Test update_agenda (Add tasks)
    print("\n=== 5.1 Testing Update Agenda (Add tasks) ===")
    # Create a new active agenda
    a_res2 = a_engine.create_agenda([{"description": "T1"}])
    aid2 = a_res2["agenda_id"]
    
    a_engine.update_agenda(aid2, new_tasks=[{"description": "T2"}])
    details2 = a_engine.get_agenda(aid2)
    assert len(details2["tasks"]) == 2
    print("✅ Added task to active agenda")

    # Deactivate irreversibly
    a_engine.update_agenda(aid2, is_active=False)
    details2 = a_engine.get_agenda(aid2)
    assert details2["is_active"] is False
    
    # Try to reactivate
    reactivate_res = a_engine.update_agenda(aid2, is_active=True)
    assert reactivate_res["status"] == "error"
    print("✅ Reactivation blocked")

    # Try to add task to inactive
    add_to_inactive = a_engine.update_agenda(aid2, new_tasks=[{"description": "T3"}])
    assert add_to_inactive["status"] == "error"
    print("✅ Adding task to inactive agenda blocked")

    # 6. Delete agenda
    print("\n=== 6. Deleting Agenda ===")
    
    # Try deleting aid2 which is inactive (from previous step)
    del_res = a_engine.delete_agenda(aid2)
    print(f"Delete Inactive Result: {del_res}")
    assert del_res["status"] == "success"

    # Create a new active agenda and try to delete it
    a_res3 = a_engine.create_agenda([{"description": "Delete Me?"}])
    aid3 = a_res3["agenda_id"]

    # Test create_agenda_memory_relations explicitly
    print("\n=== Testing create_agenda_memory_relations ===")
    a_engine.create_agenda_memory_relations([(aid3, memory_id)])
    related = a_engine.get_agenda_related_memories(aid3)
    assert memory_id in related
    print("✅ Explicit relation creation succeeded")

    del_active_res = a_engine.delete_agenda(aid3)
    print(f"Delete Active Result: {del_active_res}")
    assert del_active_res["status"] == "error"
    assert "Cannot delete active agenda" in del_active_res["message"]
    print("✅ Deletion of active agenda blocked")

    # Now deactivate and delete
    a_engine.update_agenda(aid3, is_active=False)
    del_inactive_res = a_engine.delete_agenda(aid3)
    print(f"Delete After Deactivation Result: {del_inactive_res}")
    assert del_inactive_res["status"] == "success"
    print("✅ Deletion of inactive agenda succeeded")

    # Also delete the first one
    a_engine.delete_agenda(agenda_id)
    print(f"Delete First Agenda Result: {a_engine.delete_agenda(agenda_id)}")
    
    agendas_after = a_engine.list_agendas(active_only=False)
    assert not any(a["id"] == agenda_id for a in agendas_after)
    assert not any(a["id"] == aid2 for a in agendas_after)
    assert not any(a["id"] == aid3 for a in agendas_after)

    print("\n✅ All agenda tests passed!")


if __name__ == "__main__":
    test_agenda()
