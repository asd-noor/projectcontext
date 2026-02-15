#!/usr/bin/env python3
"""Test script for Agenda functionality"""

from agentmemory.agenda import AgendaEngine


def test_agenda():
    print("Initializing Engine...")
    a_engine = AgendaEngine()

    # 1. Create an agenda
    print("\n=== 1. Creating Agenda ===")
    tasks = [
        {"details": "Task 1 (Required)", "is_optional": False},
        {
            "details": "Task 2 (Optional)",
            "is_optional": True,
            "acceptance_guard": "Must be optional",
        },
        {"details": "Task 3 (Required)", "is_optional": False},
    ]
    a_result = a_engine.create_agenda(tasks=tasks, title="My Plan", description="A test plan")
    agenda_id = a_result["agenda_id"]
    print(f"Created agenda ID: {agenda_id}")

    # 2. List agendas
    print("\n=== 2. Listing Agendas ===")
    agendas = a_engine.list_agendas(active_only=True)
    print(f"Active agendas: {agendas}")
    assert any(a["id"] == agenda_id for a in agendas)
    
    # Verify title/description
    my_agenda = next(a for a in agendas if a["id"] == agenda_id)
    assert my_agenda["title"] == "My Plan"
    assert my_agenda["description"] == "A test plan"

    # 3. Get agenda details
    print("\n=== 3. Getting Agenda Details ===")
    details = a_engine.get_agenda(agenda_id)
    print(f"Agenda Details: {details}")
    assert len(details["tasks"]) == 3
    assert details["title"] == "My Plan"

    # 4. Test Search
    print("\n=== 4. Testing Search ===")
    # Search by description
    results_desc = a_engine.search_agendas("test plan")
    print(f"Search 'test plan' (Description): {len(results_desc)} results")
    assert any(a["id"] == agenda_id for a in results_desc)

    # Search by title
    results_title = a_engine.search_agendas("My Plan")
    print(f"Search 'My Plan' (Title): {len(results_title)} results")
    assert any(a["id"] == agenda_id for a in results_title)

    # Search by task detail (should NOT find anything)
    results_task = a_engine.search_agendas("Task 2")
    print(f"Search 'Task 2' (Task Detail): {len(results_task)} results")
    assert len(results_task) == 0

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

    # 6. Test update_agenda (Add tasks)
    print("\n=== 6. Testing Update Agenda (Add tasks) ===")
    # Create a new active agenda
    a_res2 = a_engine.create_agenda([{"details": "T1"}], title="Agenda 2")
    aid2 = a_res2["agenda_id"]
    
    # Update title (SHOULD update search index now)
    a_engine.update_agenda(aid2, title="Agenda 2 Updated")
    details2 = a_engine.get_agenda(aid2)
    assert details2["title"] == "Agenda 2 Updated"
    
    # Check if search index updated
    results_upd = a_engine.search_agendas("Updated")
    assert any(a["id"] == aid2 for a in results_upd)

    # Update description (SHOULD also update search index)
    a_engine.update_agenda(aid2, description="Now with Updated description")
    results_desc_upd = a_engine.search_agendas("Updated")
    assert any(a["id"] == aid2 for a in results_desc_upd)

    a_engine.update_agenda(aid2, new_tasks=[{"details": "T2"}])
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
    add_to_inactive = a_engine.update_agenda(aid2, new_tasks=[{"details": "T3"}])
    assert add_to_inactive["status"] == "error"
    print("✅ Adding task to inactive agenda blocked")

    # 7. Delete agenda
    print("\n=== 7. Deleting Agenda ===")
    
    # Try deleting aid2 which is inactive (from previous step)
    del_res = a_engine.delete_agenda(aid2)
    print(f"Delete Inactive Result: {del_res}")
    assert del_res["status"] == "success"
    
    # Check search index cleaned
    results_del = a_engine.search_agendas("Agenda 2 Updated")
    assert not any(a["id"] == aid2 for a in results_del)

    # Create a new active agenda and try to delete it
    a_res3 = a_engine.create_agenda([{"details": "Delete Me?"}])
    aid3 = a_res3["agenda_id"]

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

    print("\n✅ All agenda tests passed!")


if __name__ == "__main__":
    test_agenda()
