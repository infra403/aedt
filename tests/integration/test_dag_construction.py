"""Integration tests for DAG construction end-to-end."""
import os
import tempfile
from pathlib import Path

import pytest

from aedt.core.config_manager import ConfigManager
from aedt.core.logger import AEDTLogger
from aedt.domain.dependency_analyzer import DependencyAnalyzer
from aedt.domain.epic_parser import EpicParser
from aedt.domain.exceptions import CircularDependencyError, InvalidDependencyError


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory with Epic files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        epics_dir = Path(tmpdir) / 'docs' / 'epics'
        epics_dir.mkdir(parents=True)

        # Epic 1: No dependencies
        (epics_dir / 'epic-001.md').write_text("""---
epic_id: 1
title: "Foundation"
depends_on: []
priority: HIGH
---

# Epic 1: Foundation
""")

        # Epic 2: Depends on 1
        (epics_dir / 'epic-002.md').write_text("""---
epic_id: 2
title: "Parsing"
depends_on: [1]
priority: MEDIUM
---

# Epic 2: Parsing
""")

        # Epic 3: Depends on 1
        (epics_dir / 'epic-003.md').write_text("""---
epic_id: 3
title: "Analysis"
depends_on: [1]
priority: MEDIUM
---

# Epic 3: Analysis
""")

        # Epic 4: Depends on 2 and 3
        (epics_dir / 'epic-004.md').write_text("""---
epic_id: 4
title: "Execution"
depends_on: [2, 3]
priority: HIGH
---

# Epic 4: Execution
""")

        yield tmpdir


@pytest.fixture
def config_manager(temp_project_dir):
    """Create ConfigManager for testing."""
    config_dir = Path(temp_project_dir) / '.aedt'
    config_dir.mkdir()

    config_file = config_dir / 'config.yaml'
    config_file.write_text("""
version: "1.0.0"
epic_docs_path: docs/epics/
epic_file_pattern: epic-*.md

subagent:
  max_concurrent: 5
  timeout: 3600
  model: claude-sonnet-4

quality_gates:
  pre_commit: []
  epic_complete: []
  pre_merge: []

git:
  worktree_base: ".aedt/worktrees"
  branch_prefix: "epic"
  auto_cleanup: true
""")

    return ConfigManager(config_file)


@pytest.fixture
def logger(temp_project_dir):
    """Create AEDTLogger for testing."""
    log_dir = Path(temp_project_dir) / '.aedt' / 'logs'
    return AEDTLogger(log_dir=log_dir, log_level="INFO")


@pytest.fixture
def epic_parser(config_manager, logger):
    """Create EpicParser instance."""
    return EpicParser(config_manager, logger)


@pytest.fixture
def dependency_analyzer(logger):
    """Create DependencyAnalyzer instance."""
    return DependencyAnalyzer(logger)


class TestEpicDAGConstructionE2E:
    """End-to-end tests for Epic DAG construction."""

    def test_full_epic_parsing_to_dag_flow(
        self, epic_parser, dependency_analyzer, temp_project_dir
    ):
        """Test complete flow: parse Epics → build DAG (AC1)."""
        # Step 1: Parse Epics
        epics = epic_parser.parse_epics(temp_project_dir)
        assert len(epics) == 4

        # Step 2: Build DAG
        dag = dependency_analyzer.build_epic_dag(epics)

        # Verify DAG structure
        assert dag.get_node_count() == 4
        assert dag.get_edge_count() == 4

        # Verify Epic 1 has no dependencies
        assert dag.edges["1"] == []

        # Verify Epic 2 and 3 depend on Epic 1
        assert "1" in dag.edges["2"]
        assert "1" in dag.edges["3"]

        # Verify Epic 4 depends on Epic 2 and 3
        assert "2" in dag.edges["4"]
        assert "3" in dag.edges["4"]

    def test_topological_sort_execution_order(
        self, epic_parser, dependency_analyzer, temp_project_dir
    ):
        """Test topological sort provides correct execution order."""
        epics = epic_parser.parse_epics(temp_project_dir)
        dag = dependency_analyzer.build_epic_dag(epics)

        # Get topological sort
        sorted_epics = dag.topological_sort()
        sorted_ids = [epic.id for epic in sorted_epics]

        # Epic 1 should come before all others
        assert sorted_ids.index("1") < sorted_ids.index("2")
        assert sorted_ids.index("1") < sorted_ids.index("3")
        assert sorted_ids.index("1") < sorted_ids.index("4")

        # Epic 4 should come last (depends on 2 and 3)
        assert sorted_ids.index("4") == 3

    def test_parallel_execution_identification(
        self, epic_parser, dependency_analyzer, temp_project_dir
    ):
        """Test identifying parallel-executable Epics."""
        epics = epic_parser.parse_epics(temp_project_dir)
        dag = dependency_analyzer.build_epic_dag(epics)

        # Initially, only Epic 1 can run
        parallel = dag.get_parallel_nodes(set())
        parallel_ids = {epic.id for epic in parallel}
        assert parallel_ids == {"1"}

        # After Epic 1 completes, Epic 2 and 3 can run in parallel
        parallel = dag.get_parallel_nodes({"1"})
        parallel_ids = {epic.id for epic in parallel}
        assert parallel_ids == {"2", "3"}

        # After 1, 2, 3 complete, Epic 4 can run
        parallel = dag.get_parallel_nodes({"1", "2", "3"})
        parallel_ids = {epic.id for epic in parallel}
        assert parallel_ids == {"4"}


class TestCircularDependencyDetection:
    """Test circular dependency detection in real Epic files (AC2)."""

    def test_circular_dependency_epic_files(
        self, config_manager, logger, temp_project_dir
    ):
        """Test detecting circular dependencies from Epic files (AC2)."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'

        # Create Epics with circular dependency
        (epics_dir / 'epic-005.md').write_text("""---
epic_id: 5
title: "Epic 5"
depends_on: [6]
---

# Epic 5
""")

        (epics_dir / 'epic-006.md').write_text("""---
epic_id: 6
title: "Epic 6"
depends_on: [5]
---

# Epic 6
""")

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)

        # Should raise CircularDependencyError
        with pytest.raises(CircularDependencyError) as exc_info:
            analyzer.build_epic_dag(epics)

        # Verify error contains cycle information
        assert "5" in str(exc_info.value) or "6" in str(exc_info.value)
        assert exc_info.value.cycle_path

    def test_self_referencing_epic(self, config_manager, logger, temp_project_dir):
        """Test detecting self-referencing Epic."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'

        (epics_dir / 'epic-007.md').write_text("""---
epic_id: 7
title: "Epic 7"
depends_on: [7]
---

# Epic 7
""")

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)

        with pytest.raises(CircularDependencyError):
            analyzer.build_epic_dag(epics)


class TestInvalidDependencyDetection:
    """Test invalid dependency detection in real Epic files (AC3)."""

    def test_missing_dependency_epic_file(
        self, config_manager, logger, temp_project_dir
    ):
        """Test detecting missing dependency from Epic file (AC3)."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'

        # Epic 8 depends on non-existent Epic 99
        (epics_dir / 'epic-008.md').write_text("""---
epic_id: 8
title: "Epic 8"
depends_on: [99]
---

# Epic 8
""")

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)

        # Should raise InvalidDependencyError
        with pytest.raises(InvalidDependencyError) as exc_info:
            analyzer.build_epic_dag(epics)

        # Verify error details
        assert exc_info.value.missing_epic_id == "99"
        assert exc_info.value.source_epic_id == "8"
        assert "Epic 8" in str(exc_info.value)
        assert "Epic 99" in str(exc_info.value)


class TestComplexDAGScenarios:
    """Test complex DAG scenarios."""

    def test_deep_dependency_chain(self, config_manager, logger, temp_project_dir):
        """Test deep linear dependency chain."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'

        # Create chain: 10 → 11 → 12 → 13 → 14
        for i in range(10, 15):
            deps = [] if i == 10 else [i - 1]
            (epics_dir / f'epic-{i:03d}.md').write_text(f"""---
epic_id: {i}
title: "Epic {i}"
depends_on: {deps}
---

# Epic {i}
""")

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # Verify chain length
        assert dag.get_node_count() == 9  # 1-4 from fixture + 10-14

        # Verify topological order
        sorted_epics = dag.topological_sort()
        chain_ids = [e.id for e in sorted_epics if e.id in ["10", "11", "12", "13", "14"]]
        assert chain_ids == ["10", "11", "12", "13", "14"]

    def test_mixed_dependencies_real_project(
        self, config_manager, logger, temp_project_dir
    ):
        """Test mixed dependency patterns resembling real project."""
        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'

        # Epic 20: Common foundation
        # Epic 21, 22, 23: Parallel features depending on 20
        # Epic 24: Integration depending on all features

        for i in range(20, 24):
            deps = [] if i == 20 else ["20"]
            (epics_dir / f'epic-{i:03d}.md').write_text(f"""---
epic_id: {i}
title: "Epic {i}"
depends_on: {deps}
---

# Epic {i}
""")

        # Epic 24 depends on 21, 22, 23
        (epics_dir / 'epic-024.md').write_text("""---
epic_id: 24
title: "Epic 24"
depends_on: [21, 22, 23]
---

# Epic 24
""")

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # After Epic 20 completes, 21, 22, 23 can run in parallel
        parallel = dag.get_parallel_nodes({"20"})
        parallel_ids = {e.id for e in parallel if e.id in ["21", "22", "23"]}
        assert parallel_ids == {"21", "22", "23"}

        # Epic 24 requires all three features
        parallel = dag.get_parallel_nodes({"20", "21", "22", "23"})
        assert any(e.id == "24" for e in parallel)


class TestParallelEpicQueries:
    """Test parallel Epic queries (Story 3.5)."""

    def test_query_parallel_epics_initial_state(
        self, config_manager, logger, temp_project_dir
    ):
        """Test querying parallel Epics when no Epics completed (AC1)."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        # Use fixture Epics: 1 (no deps), 2,3,4 (depend on 1)
        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # Query with no completed Epics
        parallel = analyzer.get_parallel_epics(dag, [])
        parallel_ids = {e.id for e in parallel}

        # Only Epic 1 has no dependencies
        assert "1" in parallel_ids

    def test_query_parallel_epics_after_completion(
        self, config_manager, logger, temp_project_dir
    ):
        """Test querying parallel Epics after some Epics complete (AC2)."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # After Epic 1 completes
        parallel = analyzer.get_parallel_epics(dag, ["1"])
        parallel_ids = {e.id for e in parallel}

        # Epics 2 and 3 depend on Epic 1, should be available
        assert "2" in parallel_ids
        assert "3" in parallel_ids
        # Epic 4 depends on both 2 and 3, so NOT available yet
        assert "4" not in parallel_ids

        # Epic 1 should NOT be in results (already completed)
        assert "1" not in parallel_ids

        # After Epics 1, 2, 3 complete, Epic 4 becomes available
        parallel = analyzer.get_parallel_epics(dag, ["1", "2", "3"])
        parallel_ids = {e.id for e in parallel}
        assert "4" in parallel_ids

    def test_query_parallel_epics_progressive_completion(
        self, config_manager, logger, temp_project_dir
    ):
        """Test progressive Epic completion scenario (AC3)."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer
        from pathlib import Path

        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'

        # Create chain: 30 → 31 → 32
        (epics_dir / 'epic-030.md').write_text("""---
epic_id: 30
title: "Epic 30"
depends_on: []
---

# Epic 30
""")

        (epics_dir / 'epic-031.md').write_text("""---
epic_id: 31
title: "Epic 31"
depends_on: [30]
---

# Epic 31
""")

        (epics_dir / 'epic-032.md').write_text("""---
epic_id: 32
title: "Epic 32"
depends_on: [30, 31]
---

# Epic 32
""")

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # Round 1: No completions
        parallel = analyzer.get_parallel_epics(dag, [])
        chain_parallel = [e.id for e in parallel if e.id in ["30", "31", "32"]]
        assert "30" in chain_parallel

        # Round 2: Epic 30 completed
        parallel = analyzer.get_parallel_epics(dag, ["30"])
        chain_parallel = [e.id for e in parallel if e.id in ["30", "31", "32"]]
        assert "31" in chain_parallel
        assert "30" not in chain_parallel  # Already completed

        # Round 3: Epics 30 and 31 completed
        parallel = analyzer.get_parallel_epics(dag, ["30", "31"])
        chain_parallel = [e.id for e in parallel if e.id in ["30", "31", "32"]]
        assert "32" in chain_parallel

    def test_query_parallel_epics_complex_scenario(
        self, config_manager, logger, temp_project_dir
    ):
        """Test complex parallel Epic scenario."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer
        from pathlib import Path

        epics_dir = Path(temp_project_dir) / 'docs' / 'epics'

        # Create diamond dependency:
        # 40 (foundation)
        # ├─ 41, 42 (parallel features)
        # └─ 43 (depends on both 41 and 42)

        (epics_dir / 'epic-040.md').write_text("""---
epic_id: 40
title: "Epic 40"
depends_on: []
---

# Epic 40
""")

        (epics_dir / 'epic-041.md').write_text("""---
epic_id: 41
title: "Epic 41"
depends_on: [40]
---

# Epic 41
""")

        (epics_dir / 'epic-042.md').write_text("""---
epic_id: 42
title: "Epic 42"
depends_on: [40]
---

# Epic 42
""")

        (epics_dir / 'epic-043.md').write_text("""---
epic_id: 43
title: "Epic 43"
depends_on: [41, 42]
---

# Epic 43
""")

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # After Epic 40, both 41 and 42 can run in parallel
        parallel = analyzer.get_parallel_epics(dag, ["40"])
        diamond_parallel = {e.id for e in parallel if e.id in ["41", "42", "43"]}
        assert diamond_parallel == {"41", "42"}

        # After Epic 41 completes, Epic 43 still waiting for 42
        parallel = analyzer.get_parallel_epics(dag, ["40", "41"])
        diamond_parallel = [e.id for e in parallel if e.id in ["41", "42", "43"]]
        assert "42" in diamond_parallel
        assert "43" not in diamond_parallel  # Still waiting for 42

        # After both 41 and 42, Epic 43 can run
        parallel = analyzer.get_parallel_epics(dag, ["40", "41", "42"])
        diamond_parallel = {e.id for e in parallel if e.id in ["41", "42", "43"]}
        assert diamond_parallel == {"43"}


class TestQueuedEpicQueries:
    """Test queued Epic queries (Story 3.6)."""

    def test_query_queued_epics_initial_state(
        self, config_manager, logger, temp_project_dir
    ):
        """Test querying queued Epics in initial state (AC1)."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        # Use fixture: Epic 1 (no deps), Epics 2,3 (depend on 1), Epic 4 (depends on 2,3)
        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # No Epics completed - all with dependencies are queued
        queued = analyzer.get_queued_epics(dag, [])
        queued_dict = {epic.id: missing for epic, missing in queued}

        # Epics 2, 3, 4 should be queued
        assert "2" in queued_dict
        assert queued_dict["2"] == ["1"]
        assert "3" in queued_dict
        assert queued_dict["3"] == ["1"]
        assert "4" in queued_dict
        assert set(queued_dict["4"]) == {"2", "3"}

    def test_query_queued_epics_with_multiple_missing(
        self, config_manager, logger, temp_project_dir
    ):
        """Test queued Epics with multiple missing dependencies (AC2)."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # Only Epic 1 completed
        queued = analyzer.get_queued_epics(dag, ["1"])
        queued_dict = {epic.id: missing for epic, missing in queued}

        # Epic 4 should have 2 missing dependencies: 2 and 3
        assert "4" in queued_dict
        assert set(queued_dict["4"]) == {"2", "3"}

    def test_queued_status_changes_with_completion(
        self, config_manager, logger, temp_project_dir
    ):
        """Test queued status updates as Epics complete (AC3)."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        # After Epic 1 and 2 complete
        queued = analyzer.get_queued_epics(dag, ["1", "2"])
        queued_dict = {epic.id: missing for epic, missing in queued}

        # Epic 4 should now only wait for Epic 3
        assert "4" in queued_dict
        assert queued_dict["4"] == ["3"]

        # After all dependencies complete, Epic 4 not queued anymore
        queued = analyzer.get_queued_epics(dag, ["1", "2", "3"])
        queued_ids = {epic.id for epic, _ in queued}
        assert "4" not in queued_ids

    def test_parallel_and_queued_coverage(
        self, config_manager, logger, temp_project_dir
    ):
        """Test parallel + queued covers all non-completed Epics."""
        from aedt.domain.epic_parser import EpicParser
        from aedt.domain.dependency_analyzer import DependencyAnalyzer

        parser = EpicParser(config_manager, logger)
        analyzer = DependencyAnalyzer(logger)

        epics = parser.parse_epics(temp_project_dir)
        dag = analyzer.build_epic_dag(epics)

        completed = ["1"]
        parallel = analyzer.get_parallel_epics(dag, completed)
        queued = analyzer.get_queued_epics(dag, completed)

        parallel_ids = {e.id for e in parallel}
        queued_ids = {e.id for e, _ in queued}
        all_epic_ids = {e.id for e in epics}

        # parallel + queued + completed = all epics
        assert parallel_ids | queued_ids | set(completed) == all_epic_ids

        # No overlap between parallel and queued
        assert parallel_ids.isdisjoint(queued_ids)
