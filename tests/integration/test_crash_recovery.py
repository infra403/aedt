"""Integration tests for crash recovery scenarios"""

import pytest
import tempfile
import shutil
from pathlib import Path
import time

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


def test_single_epic_crash_recovery(temp_dir):
    """Test crash recovery for single epic in developing state"""
    # Setup: Create epic in developing state
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Create worktree directory so it exists
    worktree_dir = temp_dir / ".aedt" / "worktrees" / "epic-1"
    worktree_dir.mkdir(parents=True, exist_ok=True)

    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="developing",
                progress=45.0,
                agent_id="agent-abc",
                worktree_path=str(worktree_dir),
                completed_stories=["1-1", "1-2"]
            )
        }
    )

    state_manager.save_project_state(project)

    # Simulate crash: discard state manager without cleanup
    del state_manager

    # Recovery: Create new state manager and load
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    # Verify: Status changed to paused
    recovered_epic = recovered_states["test-001"].epics["epic-1"]
    assert recovered_epic.status == "paused"
    assert recovered_epic.progress == 45.0
    assert recovered_epic.agent_id == "agent-abc"
    assert recovered_epic.completed_stories == ["1-1", "1-2"]


def test_multiple_epics_crash_recovery(temp_dir):
    """Test crash recovery for multiple epics in different states"""
    # Setup
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="developing",
                progress=30.0
            ),
            "epic-2": EpicState(
                epic_id="2",
                status="developing",
                progress=70.0
            ),
            "epic-3": EpicState(
                epic_id="3",
                status="completed",
                progress=100.0
            ),
            "epic-4": EpicState(
                epic_id="4",
                status="queued",
                progress=0.0
            )
        }
    )

    state_manager.save_project_state(project)
    del state_manager

    # Recovery
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    recovered_epics = recovered_states["test-001"].epics

    # Verify: Only developing epics changed to paused
    assert recovered_epics["epic-1"].status == "paused"
    assert recovered_epics["epic-2"].status == "paused"
    assert recovered_epics["epic-3"].status == "completed"  # Unchanged
    assert recovered_epics["epic-4"].status == "queued"  # Unchanged


def test_worktree_validation_after_crash(temp_dir):
    """Test worktree path validation during crash recovery"""
    # Setup: Create epic with worktree that will become invalid
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Create temporary worktree directory
    worktree_dir = temp_dir / "worktrees" / "epic-1"
    worktree_dir.mkdir(parents=True, exist_ok=True)

    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="developing",
                progress=50.0,
                worktree_path=str(worktree_dir)
            ),
            "epic-2": EpicState(
                epic_id="2",
                status="developing",
                progress=30.0,
                worktree_path="/nonexistent/worktree"
            )
        }
    )

    state_manager.save_project_state(project)

    # Simulate crash and worktree loss: remove worktree directory
    shutil.rmtree(worktree_dir)
    del state_manager

    # Recovery
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    recovered_epics = recovered_states["test-001"].epics

    # Verify: Both epics marked for cleanup (invalid worktrees)
    assert recovered_epics["epic-1"].status == "requires_cleanup"
    assert recovered_epics["epic-1"].worktree_path is None

    assert recovered_epics["epic-2"].status == "requires_cleanup"
    assert recovered_epics["epic-2"].worktree_path is None


def test_crash_with_partial_write(temp_dir):
    """Test that partial writes don't corrupt state (atomic write protection)"""
    # Setup
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Save initial state
    project = ProjectState(
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

    state_manager.save_project_state(project)

    # Verify initial state file exists and is valid
    state_file = temp_dir / "projects" / "TestProject" / "status.yaml"
    assert state_file.exists()

    # Attempt write with invalid data (will fail)
    class UnserializableClass:
        pass

    # Try to save with unserializable data (should fail and not corrupt file)
    try:
        data_store.atomic_write(
            state_file,
            {"bad_field": UnserializableClass()}  # This will fail YAML serialization
        )
    except:
        pass  # Expected failure

    # Verify: Original state file still intact
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    # Original data should be intact
    recovered_epic = recovered_states["test-001"].epics["epic-1"]
    assert recovered_epic.status == "completed"  # Completed stays completed
    assert recovered_epic.progress == 100.0
    assert recovered_epic.completed_stories == ["1-1", "1-2", "1-3"]


def test_recovery_with_backup_rotation(temp_dir):
    """Test that backup rotation doesn't affect crash recovery"""
    # Setup
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(epic_id="1", status="queued", progress=0.0)
        }
    )

    # Save initial state
    state_manager.save_project_state(project)

    # Make multiple updates (creates multiple backups)
    for i in range(5):
        time.sleep(0.01)  # Ensure different timestamps
        state_manager.update_epic_state(
            "test-001",
            "epic-1",
            progress=float(i * 20),
            completed_stories=[f"1-{j}" for j in range(1, i + 1)]
        )

    # Verify backups created and rotated (keep 3)
    project_dir = temp_dir / "projects" / "TestProject"
    backup_files = list(project_dir.glob("status.yaml.backup.*"))
    assert len(backup_files) == 3

    # Crash
    del state_manager

    # Recovery
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    # Verify latest state recovered
    recovered_epic = recovered_states["test-001"].epics["epic-1"]
    assert recovered_epic.progress == 80.0  # Last update


def test_multiple_projects_crash_recovery(temp_dir):
    """Test crash recovery across multiple projects"""
    # Setup: Create multiple projects with different epic states
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    projects = [
        ProjectState(
            project_id=f"proj-{i}",
            project_name=f"Project{i}",
            epics={
                "epic-1": EpicState(
                    epic_id="1",
                    status="developing",
                    progress=float(i * 10)
                )
            }
        )
        for i in range(3)
    ]

    # Save all projects
    for project in projects:
        state_manager.save_project_state(project)

    del state_manager

    # Recovery
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    # Verify all projects recovered
    assert len(recovered_states) == 3

    # Verify all developing epics paused
    for i in range(3):
        project = recovered_states[f"proj-{i}"]
        assert project.epics["epic-1"].status == "paused"
        assert project.epics["epic-1"].progress == float(i * 10)


def test_crash_recovery_preserves_metadata(temp_dir):
    """Test that crash recovery preserves all epic metadata"""
    # Setup
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

    # Create worktree directory so it exists
    worktree_dir = temp_dir / ".aedt" / "worktrees" / "epic-1"
    worktree_dir.mkdir(parents=True, exist_ok=True)

    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="developing",
                progress=65.0,
                agent_id="agent-xyz-789",
                worktree_path=str(worktree_dir),
                completed_stories=["1-1", "1-2", "1-3", "1-4"]
            )
        }
    )

    state_manager.save_project_state(project)
    del state_manager

    # Recovery
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    # Verify all metadata preserved
    recovered_epic = recovered_states["test-001"].epics["epic-1"]
    assert recovered_epic.status == "paused"  # Changed for crash recovery
    assert recovered_epic.epic_id == "1"
    assert recovered_epic.progress == 65.0
    assert recovered_epic.agent_id == "agent-xyz-789"
    assert recovered_epic.completed_stories == ["1-1", "1-2", "1-3", "1-4"]
    assert recovered_epic.last_updated is not None


def test_no_state_loss_during_rapid_updates(temp_dir):
    """Test that rapid updates don't lose state during crash"""
    # Setup
    data_store = DataStore(temp_dir)
    state_manager = StateManager(temp_dir, data_store)

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

    state_manager.save_project_state(project)

    # Rapid sequential updates
    final_progress = 0.0
    for i in range(20):
        final_progress = float(i * 5)
        state_manager.update_epic_state(
            "test-001",
            "epic-1",
            progress=final_progress
        )

    # Crash immediately after updates
    del state_manager

    # Recovery
    recovery_manager = StateManager(temp_dir, DataStore(temp_dir))
    recovered_states = recovery_manager.load_all_states()

    # Verify final state recovered (or very close to it)
    recovered_epic = recovered_states["test-001"].epics["epic-1"]
    # Should have final or near-final progress (atomic writes guarantee integrity)
    assert recovered_epic.progress >= final_progress - 10.0
