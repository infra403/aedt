"""Integration tests for state persistence"""

import pytest
import tempfile
import shutil
from pathlib import Path

from aedt.core.data_store import DataStore
from aedt.core.state_manager import StateManager, EpicState, ProjectState


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    tmp_dir = Path(tempfile.mkdtemp())
    yield tmp_dir
    # Cleanup
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)


def test_full_state_persistence_flow(temp_dir):
    """Test complete flow: create -> save -> load -> verify"""
    # Step 1: Initialize components
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Create worktree directories so they exist
    worktree1 = temp_dir / ".aedt" / "worktrees" / "epic-1"
    worktree2 = temp_dir / ".aedt" / "worktrees" / "epic-2"
    worktree1.mkdir(parents=True, exist_ok=True)
    worktree2.mkdir(parents=True, exist_ok=True)

    # Step 2: Create project state with multiple epics
    project = ProjectState(
        project_id="aedt-001",
        project_name="AEDT",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="completed",
                progress=100.0,
                agent_id="agent-abc123",
                worktree_path=str(worktree1),
                completed_stories=["1-1", "1-2", "1-3", "1-4", "1-5"]
            ),
            "epic-2": EpicState(
                epic_id="2",
                status="developing",
                progress=40.0,
                agent_id="agent-def456",
                worktree_path=str(worktree2),
                completed_stories=["2-1", "2-2"]
            ),
            "epic-3": EpicState(
                epic_id="3",
                status="queued",
                progress=0.0
            )
        }
    )

    # Step 3: Save state
    result = state_manager.save_project_state(project)
    assert result is True

    # Step 4: Create new state manager (simulate restart)
    new_state_manager = StateManager(temp_dir, DataStore(temp_dir))

    # Step 5: Load state
    loaded_states = new_state_manager.load_all_states()

    # Step 6: Verify all data preserved
    assert "aedt-001" in loaded_states
    loaded_project = loaded_states["aedt-001"]

    assert loaded_project.project_id == "aedt-001"
    assert loaded_project.project_name == "AEDT"
    assert len(loaded_project.epics) == 3

    # Verify Epic 1 (completed - should remain completed)
    epic1 = loaded_project.epics["epic-1"]
    assert epic1.status == "completed"  # Terminal state, not affected by validation
    assert epic1.progress == 100.0
    assert len(epic1.completed_stories) == 5

    # Verify Epic 2 (developing -> paused after crash recovery)
    epic2 = loaded_project.epics["epic-2"]
    assert epic2.status == "paused"  # Crash recovery
    assert epic2.progress == 40.0
    assert len(epic2.completed_stories) == 2

    # Verify Epic 3 (queued)
    epic3 = loaded_project.epics["epic-3"]
    assert epic3.status == "queued"
    assert epic3.progress == 0.0


def test_atomic_write_during_concurrent_updates(temp_dir):
    """Test atomic writes preserve data integrity during rapid updates"""
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Create initial project
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="developing",
                progress=0.0
            )
        }
    )

    # Save initial state
    state_manager.save_project_state(project)

    # Perform rapid sequential updates
    for i in range(10):
        state_manager.update_epic_state(
            "test-001",
            "epic-1",
            progress=float(i * 10),
            completed_stories=[f"1-{j}" for j in range(1, i + 1)]
        )

    # Verify final state
    final_project = state_manager.get_project_state("test-001")
    assert final_project.epics["epic-1"].progress == 90.0
    assert len(final_project.epics["epic-1"].completed_stories) == 9

    # Verify multiple backups created
    project_dir = temp_dir / "projects" / "TestProject"
    backup_files = list(project_dir.glob("status.yaml.backup.*"))
    assert len(backup_files) >= 3  # Should have at least 3 backups


def test_crash_recovery_scenario(temp_dir):
    """Test crash recovery: system restart after crash during epic development"""
    # Step 1: Setup - create state with developing epics
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Create worktree directories so they exist
    worktree1 = temp_dir / ".aedt" / "worktrees" / "epic-1"
    worktree2 = temp_dir / ".aedt" / "worktrees" / "epic-2"
    worktree1.mkdir(parents=True, exist_ok=True)
    worktree2.mkdir(parents=True, exist_ok=True)

    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="developing",
                progress=30.0,
                agent_id="agent-123",
                worktree_path=str(worktree1)
            ),
            "epic-2": EpicState(
                epic_id="2",
                status="developing",
                progress=60.0,
                agent_id="agent-456",
                worktree_path=str(worktree2)
            ),
            "epic-3": EpicState(
                epic_id="3",
                status="completed",
                progress=100.0
            )
        }
    )

    state_manager.save_project_state(project)

    # Step 2: Simulate crash (don't cleanup, just discard state_manager)
    del state_manager

    # Step 3: Simulate restart - create new state manager
    recovery_data_store = DataStore(temp_dir)
    recovery_state_manager = StateManager(temp_dir, recovery_data_store)

    # Step 4: Load states (triggers crash recovery)
    recovered_states = recovery_state_manager.load_all_states()

    # Step 5: Verify crash recovery behavior
    recovered_project = recovered_states["test-001"]

    # Developing epics should be paused
    assert recovered_project.epics["epic-1"].status == "paused"
    assert recovered_project.epics["epic-2"].status == "paused"

    # Completed epic should remain completed
    assert recovered_project.epics["epic-3"].status == "completed"

    # Progress should be preserved
    assert recovered_project.epics["epic-1"].progress == 30.0
    assert recovered_project.epics["epic-2"].progress == 60.0


def test_invalid_worktree_cleanup(temp_dir):
    """Test that invalid worktree paths trigger cleanup status for non-terminal states"""
    # Step 1: Create state with worktree path
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Use a path that doesn't exist, with queued status (not terminal)
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="queued",
                progress=0.0,
                worktree_path="/nonexistent/worktree/path"
            )
        }
    )

    state_manager.save_project_state(project)

    # Step 2: Load in new state manager (triggers validation)
    new_state_manager = StateManager(temp_dir, DataStore(temp_dir))
    loaded_states = new_state_manager.load_all_states()

    # Step 3: Verify epic marked for cleanup
    loaded_epic = loaded_states["test-001"].epics["epic-1"]
    assert loaded_epic.status == "requires_cleanup"
    assert loaded_epic.worktree_path is None


def test_backup_recovery_from_corruption(temp_dir):
    """Test recovery from backup when state file becomes corrupted"""
    # Step 1: Create and save valid state
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    original_project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="completed",
                progress=100.0,
                completed_stories=["1-1", "1-2", "1-3"]
            )
        }
    )

    state_manager.save_project_state(original_project)

    # Step 2: Make an update (creates backup)
    state_manager.update_epic_state(
        "test-001",
        "epic-1",
        completed_stories=["1-1", "1-2", "1-3", "1-4"]
    )

    # Step 3: Corrupt the state file
    state_file = temp_dir / "projects" / "TestProject" / "status.yaml"
    with open(state_file, 'w') as f:
        f.write("this is not valid yaml: [unclosed bracket")

    # Step 4: Load state (should recover from backup)
    recovery_state_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_state_manager.load_all_states()

    # Step 5: Verify recovery successful
    assert "test-001" in recovered_states
    recovered_project = recovered_states["test-001"]
    assert recovered_project.project_name == "TestProject"
    assert "epic-1" in recovered_project.epics

    # Backup should have original or previous update data
    recovered_epic = recovered_project.epics["epic-1"]
    assert recovered_epic.epic_id == "1"
    assert recovered_epic.status in ["paused", "completed", "requires_cleanup"]


def test_multiple_projects_persistence(temp_dir):
    """Test persistence of multiple projects simultaneously"""
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Create multiple projects
    projects = {
        "project-a": ProjectState(
            project_id="proj-a",
            project_name="ProjectA",
            epics={
                "epic-1": EpicState(epic_id="1", status="completed", progress=100.0)
            }
        ),
        "project-b": ProjectState(
            project_id="proj-b",
            project_name="ProjectB",
            epics={
                "epic-1": EpicState(epic_id="1", status="queued", progress=0.0),
                "epic-2": EpicState(epic_id="2", status="developing", progress=50.0)
            }
        ),
        "project-c": ProjectState(
            project_id="proj-c",
            project_name="ProjectC",
            epics={
                "epic-1": EpicState(epic_id="1", status="failed", progress=0.0)
            }
        )
    }

    # Save all projects
    for project in projects.values():
        state_manager.save_project_state(project)

    # Load in new state manager
    new_state_manager = StateManager(temp_dir, DataStore(temp_dir))
    loaded_states = new_state_manager.load_all_states()

    # Verify all projects loaded correctly
    assert len(loaded_states) == 3
    assert "proj-a" in loaded_states
    assert "proj-b" in loaded_states
    assert "proj-c" in loaded_states

    # Verify project details
    assert loaded_states["proj-a"].project_name == "ProjectA"
    assert len(loaded_states["proj-b"].epics) == 2
    assert loaded_states["proj-c"].epics["epic-1"].status == "failed"
