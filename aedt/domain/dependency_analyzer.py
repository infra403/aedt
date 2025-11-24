"""Dependency Analyzer for building and validating DAGs."""
import time
from typing import List, Optional, Set, Tuple

from aedt.core.logger import AEDTLogger
from aedt.domain.exceptions import (
    CircularDependencyError,
    InvalidDependencyError,
    InvalidPrerequisiteError,
)
from aedt.domain.models.dag import DAG
from aedt.domain.models.epic import Epic
from aedt.domain.models.story import Story


class DependencyAnalyzer:
    """Analyzes and builds dependency graphs for Epics and Stories."""

    def __init__(self, logger: AEDTLogger):
        """
        Initialize DependencyAnalyzer.

        Args:
            logger: AEDTLogger instance
        """
        self.aedt_logger = logger
        self.logger = logger.get_logger("dependency_analyzer")

    def build_epic_dag(self, epics: List[Epic]) -> DAG:
        """
        Build a DAG from Epic dependencies.

        Args:
            epics: List of Epic objects

        Returns:
            DAG object representing Epic dependencies

        Raises:
            InvalidDependencyError: If an Epic depends on a non-existent Epic
            CircularDependencyError: If a circular dependency is detected
        """
        start_time = time.time()
        self.logger.info(f"Building Epic DAG from {len(epics)} Epics")

        dag = DAG()

        # Build Epic ID set for validation
        epic_ids = {epic.id for epic in epics}

        # Add all nodes
        for epic in epics:
            dag.add_node(epic.id, epic)
            self.logger.debug(f"Added Epic node: {epic.id} - {epic.title}")

        # Add edges and validate dependencies
        for epic in epics:
            for dep_id in epic.depends_on:
                # Validate dependency exists
                if dep_id not in epic_ids:
                    error_msg = (
                        f"Epic {epic.id} depends on Epic {dep_id}, "
                        f"but Epic {dep_id} not found"
                    )
                    self.logger.error(error_msg)
                    raise InvalidDependencyError(
                        error_msg, missing_epic_id=dep_id, source_epic_id=epic.id
                    )

                dag.add_edge(epic.id, dep_id)
                self.logger.debug(f"Added edge: Epic {epic.id} → Epic {dep_id}")

        # Validate DAG (check for cycles)
        is_valid, error_msg = self.validate_dag(dag)
        if not is_valid:
            self.logger.error(f"DAG validation failed: {error_msg}")
            cycle_path = dag.find_cycle()
            raise CircularDependencyError(error_msg, cycle_path=cycle_path)

        elapsed = time.time() - start_time
        self.logger.info(
            f"Epic DAG built successfully: {dag.get_node_count()} nodes, "
            f"{dag.get_edge_count()} edges, took {elapsed*1000:.2f}ms"
        )

        return dag

    def validate_dag(self, dag: DAG) -> Tuple[bool, Optional[str]]:
        """
        Validate DAG structure (no cycles).

        Args:
            dag: DAG object to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if dag.has_cycle():
            cycle_path = dag.find_cycle()
            if cycle_path:
                cycle_str = " → ".join(cycle_path)
                error_msg = f"Circular dependency detected: {cycle_str}"
            else:
                error_msg = "Circular dependency detected"
            return False, error_msg

        return True, None

    def build_story_dag(self, stories: List[Story], epic_id: Optional[str] = None) -> DAG:
        """
        Build a DAG from Story dependencies (prerequisites).

        Args:
            stories: List of Story objects
            epic_id: Optional Epic ID for logging context

        Returns:
            DAG object representing Story dependencies

        Raises:
            InvalidPrerequisiteError: If a Story prerequisite references a non-existent Story
            CircularDependencyError: If a circular dependency is detected
        """
        start_time = time.time()
        epic_context = f" for Epic {epic_id}" if epic_id else ""
        self.logger.info(f"Building Story DAG{epic_context}: {len(stories)} Stories")

        dag = DAG()

        # Build Story ID set for validation
        story_ids = {story.id for story in stories}

        # Add all nodes
        for story in stories:
            dag.add_node(story.id, story)
            self.logger.debug(f"Added Story node: {story.id} - {story.title}")

        # Add edges and validate prerequisites
        for story in stories:
            for prereq_id in story.prerequisites:
                # Validate prerequisite exists
                if prereq_id not in story_ids:
                    error_msg = (
                        f"Story {story.id} has prerequisite {prereq_id}, "
                        f"but Story {prereq_id} not found in Epic"
                    )
                    self.logger.error(error_msg)
                    raise InvalidPrerequisiteError(
                        error_msg, invalid_prereq_id=prereq_id, story_id=story.id
                    )

                dag.add_edge(story.id, prereq_id)
                self.logger.debug(f"Added edge: Story {story.id} → Story {prereq_id}")

        # Validate DAG (check for cycles)
        is_valid, error_msg = self.validate_dag(dag)
        if not is_valid:
            self.logger.error(f"Story DAG validation failed: {error_msg}")
            cycle_path = dag.find_cycle()
            raise CircularDependencyError(error_msg, cycle_path=cycle_path)

        elapsed = time.time() - start_time
        self.logger.info(
            f"Story DAG built successfully{epic_context}: {dag.get_node_count()} nodes, "
            f"{dag.get_edge_count()} edges, took {elapsed*1000:.2f}ms"
        )

        return dag

    def get_parallel_stories(
        self, dag: DAG, completed_story_ids: Set[str]
    ) -> List[Story]:
        """
        Get all Stories whose prerequisites are satisfied.

        Args:
            dag: Story DAG
            completed_story_ids: Set of completed Story IDs

        Returns:
            List of Stories that can be executed in parallel
        """
        parallel_stories = dag.get_parallel_nodes(completed_story_ids)
        story_ids = [story.id for story in parallel_stories]
        self.logger.debug(
            f"Parallel Stories ({len(completed_story_ids)} completed): {story_ids}"
        )
        return parallel_stories

    def get_parallel_epics(
        self, dag: DAG, completed_epic_ids: List[str]
    ) -> List[Epic]:
        """
        Get all Epics whose dependencies are satisfied.

        Args:
            dag: Epic DAG
            completed_epic_ids: List of completed Epic IDs

        Returns:
            List of Epics that can be executed in parallel
        """
        start_time = time.time()
        completed_set = set(completed_epic_ids)

        self.logger.info(
            f"Querying parallel Epics ({len(completed_epic_ids)} completed)"
        )

        # Use DAG's get_parallel_nodes to find Epics with satisfied dependencies
        parallel_epics = dag.get_parallel_nodes(completed_set)

        # Log each Epic's dependency status
        for epic in dag.nodes.values():
            if epic.id in completed_set:
                continue  # Skip completed Epics
            deps = dag.edges.get(epic.id, [])
            if all(dep_id in completed_set for dep_id in deps):
                self.logger.debug(
                    f"Epic {epic.id}: all dependencies satisfied {deps}"
                )
            else:
                unmet = [d for d in deps if d not in completed_set]
                self.logger.debug(
                    f"Epic {epic.id}: waiting for dependencies {unmet}"
                )

        elapsed = time.time() - start_time
        epic_ids = [epic.id for epic in parallel_epics]
        self.logger.info(
            f"Found {len(parallel_epics)} parallel Epics: {epic_ids}, "
            f"took {elapsed*1000:.2f}ms"
        )

        return parallel_epics

    def get_queued_epics(
        self, dag: DAG, completed_epic_ids: List[str]
    ) -> List[Tuple[Epic, List[str]]]:
        """
        Get all Epics that are waiting for dependencies to complete.

        Args:
            dag: Epic DAG
            completed_epic_ids: List of completed Epic IDs

        Returns:
            List of tuples (Epic, missing_dependency_ids)
        """
        start_time = time.time()
        completed_set = set(completed_epic_ids)

        self.logger.info(
            f"Querying queued Epics ({len(completed_epic_ids)} completed)"
        )

        queued_epics = []
        for epic in dag.nodes.values():
            if epic.id in completed_set:
                continue  # Skip completed Epics

            # Find missing dependencies
            deps = dag.edges.get(epic.id, [])
            missing_deps = [dep_id for dep_id in deps if dep_id not in completed_set]

            if missing_deps:
                queued_epics.append((epic, missing_deps))
                self.logger.debug(
                    f"Epic {epic.id}: missing dependencies {missing_deps}"
                )

        elapsed = time.time() - start_time
        self.logger.info(
            f"Found {len(queued_epics)} queued Epics, took {elapsed*1000:.2f}ms"
        )

        return queued_epics
