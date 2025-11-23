"""Unit tests for StateManager"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

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


@pytest.fixture
def data_store(temp_dir):
    """Create DataStore instance"""
    return DataStore(temp_dir)


@pytest.fixture
def state_manager(temp_dir, data_store):
    """Create StateManager instance"""
    return StateManager(temp_dir, data_store)


def test_epic_state_initialization():
    """Test EpicState default field initialization"""
    epic = EpicState(
        epic_id="1",
        status="queued",
        progress=0.0
    )

    assert epic.epic_id == "1"
    assert epic.status == "queued"
    assert epic.progress == 0.0
    assert epic.agent_id is None
    assert epic.worktree_path is None
    assert epic.completed_stories == []
    assert epic.last_updated is not None


def test_project_state_initialization():
    """Test ProjectState default field initialization"""
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject"
    )

    assert project.project_id == "test-001"
    assert project.project_name == "TestProject"
    assert project.epics == {}
    assert project.last_updated is not None


def test_save_and_load_project_state(state_manager, temp_dir):
    """Test saving and loading project state"""
    # Create worktree directory for validation
    worktree_path = temp_dir / "worktrees" / "epic-1"
    worktree_path.mkdir(parents=True, exist_ok=True)

    # Create project state
    epic1 = EpicState(
        epic_id="1",
        status="completed",
        progress=100.0,
        agent_id="agent-123",
        worktree_path=str(worktree_path),
        completed_stories=["1-1", "1-2", "1-3"]
    )

    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={"epic-1": epic1}
    )

    # Save
    result = state_manager.save_project_state(project)
    assert result is True

    # Verify file created
    state_file = temp_dir / "projects" / "TestProject" / "status.yaml"
    assert state_file.exists()

    # Load
    loaded_states = state_manager.load_all_states()

    # Verify
    assert "test-001" in loaded_states
    loaded_project = loaded_states["test-001"]

    assert loaded_project.project_id == project.project_id
    assert loaded_project.project_name == project.project_name
    assert "epic-1" in loaded_project.epics

    loaded_epic = loaded_project.epics["epic-1"]
    assert loaded_epic.epic_id == "1"
    assert loaded_epic.status == "completed"
    assert loaded_epic.progress == 100.0
    assert loaded_epic.completed_stories == ["1-1", "1-2", "1-3"]


def test_load_all_states_empty_directory(state_manager, temp_dir):
    """Test load_all_states with no project directories"""
    # Load (should return empty dict)
    loaded_states = state_manager.load_all_states()

    assert loaded_states == {}


def test_get_project_state(state_manager):
    """Test get_project_state"""
    # Create and add project state
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject"
    )
    state_manager.projects["test-001"] = project

    # Get existing project
    retrieved = state_manager.get_project_state("test-001")
    assert retrieved is not None
    assert retrieved.project_id == "test-001"

    # Get nonexistent project
    nonexistent = state_manager.get_project_state("nonexistent")
    assert nonexistent is None


def test_update_epic_state(state_manager):
    """Test update_epic_state"""
    # Setup
    epic = EpicState(
        epic_id="1",
        status="queued",
        progress=0.0
    )
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={"epic-1": epic}
    )
    state_manager.projects["test-001"] = project

    # Update
    result = state_manager.update_epic_state(
        "test-001",
        "epic-1",
        status="developing",
        progress=50.0,
        agent_id="agent-456"
    )

    # Verify
    assert result is True

    updated_epic = state_manager.projects["test-001"].epics["epic-1"]
    assert updated_epic.status == "developing"
    assert updated_epic.progress == 50.0
    assert updated_epic.agent_id == "agent-456"


def test_update_epic_state_nonexistent_project(state_manager):
    """Test update_epic_state with nonexistent project"""
    with pytest.raises(ValueError, match="项目不存在"):
        state_manager.update_epic_state(
            "nonexistent",
            "epic-1",
            status="completed"
        )


def test_update_epic_state_nonexistent_epic(state_manager):
    """Test update_epic_state with nonexistent epic"""
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject"
    )
    state_manager.projects["test-001"] = project

    with pytest.raises(ValueError, match="Epic 不存在"):
        state_manager.update_epic_state(
            "test-001",
            "nonexistent-epic",
            status="completed"
        )


def test_crash_recovery_developing_to_paused(state_manager, temp_dir):
    """Test crash recovery: developing status changes to paused"""
    # Create project with developing epic
    epic = EpicState(
        epic_id="1",
        status="developing",
        progress=50.0,
        agent_id="agent-123"
    )
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={"epic-1": epic}
    )

    # Save
    state_manager.save_project_state(project)

    # Create new state manager (simulating restart)
    new_state_manager = StateManager(temp_dir, DataStore(temp_dir))

    # Load (triggers validation)
    loaded_states = new_state_manager.load_all_states()

    # Verify epic status changed to paused
    loaded_epic = loaded_states["test-001"].epics["epic-1"]
    assert loaded_epic.status == "paused"


def test_validate_invalid_worktree_path(state_manager):
    """Test validation marks epic as requires_cleanup if worktree invalid (non-terminal states only)"""
    # Create epic with invalid worktree path in queued state
    epic = EpicState(
        epic_id="1",
        status="queued",
        progress=0.0,
        worktree_path="/nonexistent/path/to/worktree"
    )
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={"epic-1": epic}
    )

    # Validate
    validated = state_manager._validate_state(project)

    # Verify
    validated_epic = validated.epics["epic-1"]
    assert validated_epic.status == "requires_cleanup"
    assert validated_epic.worktree_path is None


def test_backup_created_on_save(state_manager, temp_dir):
    """Test that backup is created when saving over existing state"""
    # Create initial project state
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject"
    )

    # Save initial state
    state_manager.save_project_state(project)

    # Modify and save again
    project.epics["epic-1"] = EpicState(
        epic_id="1",
        status="queued",
        progress=0.0
    )
    state_manager.save_project_state(project)

    # Verify backup created
    project_dir = temp_dir / "projects" / "TestProject"
    backup_files = list(project_dir.glob("status.yaml.backup.*"))
    assert len(backup_files) >= 1


def test_corrupted_state_recovery_from_backup(state_manager, temp_dir):
    """Test recovery from backup when state file is corrupted"""
    # Create valid project state
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={
            "epic-1": EpicState(
                epic_id="1",
                status="completed",
                progress=100.0
            )
        }
    )

    # Save initial state
    state_manager.save_project_state(project)

    # Make an update (this will create a backup of the first save)
    import time
    time.sleep(0.01)  # Ensure different timestamp
    state_manager.update_epic_state(
        "test-001",
        "epic-1",
        completed_stories=["1-1", "1-2"]
    )

    # Verify backup was created
    project_dir = temp_dir / "projects" / "TestProject"
    backup_files = list(project_dir.glob("status.yaml.backup.*"))
    assert len(backup_files) >= 1, "No backup created"

    # Corrupt the state file
    state_file = temp_dir / "projects" / "TestProject" / "status.yaml"
    with open(state_file, 'w') as f:
        f.write("corrupted: yaml: syntax: error:\n  - [unclosed")

    # Create new state manager and load (should recover from backup)
    new_state_manager = StateManager(temp_dir, DataStore(temp_dir))
    loaded_states = new_state_manager.load_all_states()

    # Verify recovery successful
    assert "test-001" in loaded_states
    loaded_project = loaded_states["test-001"]
    assert loaded_project.project_name == "TestProject"
    assert "epic-1" in loaded_project.epics


def test_load_multiple_projects(state_manager, temp_dir):
    """Test loading multiple project states"""
    # Create multiple projects
    projects = [
        ProjectState(
            project_id=f"test-{i:03d}",
            project_name=f"Project{i}",
            epics={
                "epic-1": EpicState(
                    epic_id="1",
                    status="completed",
                    progress=100.0
                )
            }
        )
        for i in range(3)
    ]

    # Save all projects
    for project in projects:
        state_manager.save_project_state(project)

    # Create new state manager and load
    new_state_manager = StateManager(temp_dir, DataStore(temp_dir))
    loaded_states = new_state_manager.load_all_states()

    # Verify all projects loaded
    assert len(loaded_states) == 3
    for i in range(3):
        assert f"test-{i:03d}" in loaded_states


def test_parse_project_state_missing_required_fields(state_manager):
    """Test _parse_project_state raises ValueError for missing fields"""
    # Missing project_id
    with pytest.raises(ValueError, match="缺少必需字段"):
        state_manager._parse_project_state({
            'project_name': 'TestProject'
        })

    # Missing project_name
    with pytest.raises(ValueError, match="缺少必需字段"):
        state_manager._parse_project_state({
            'project_id': 'test-001'
        })

    # Empty dict
    with pytest.raises(ValueError, match="项目状态数据为空"):
        state_manager._parse_project_state({})


def test_project_state_to_dict(state_manager):
    """Test _project_state_to_dict conversion"""
    epic = EpicState(
        epic_id="1",
        status="completed",
        progress=100.0,
        completed_stories=["1-1", "1-2"]
    )
    project = ProjectState(
        project_id="test-001",
        project_name="TestProject",
        epics={"epic-1": epic}
    )

    # Convert
    result = state_manager._project_state_to_dict(project)

    # Verify structure
    assert 'project_id' in result
    assert 'project_name' in result
    assert 'last_updated' in result
    assert 'epics' in result

    assert result['project_id'] == "test-001"
    assert result['project_name'] == "TestProject"
    assert 'epic-1' in result['epics']

    epic_dict = result['epics']['epic-1']
    assert epic_dict['epic_id'] == "1"
    assert epic_dict['status'] == "completed"
    assert epic_dict['progress'] == 100.0
    assert epic_dict['completed_stories'] == ["1-1", "1-2"]
