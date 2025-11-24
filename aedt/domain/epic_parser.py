"""Epic Parser - Parses BMAD Epic documents and extracts metadata."""
import glob
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

import frontmatter
import yaml
from markdown_it import MarkdownIt

from aedt.core.config_manager import ConfigManager
from aedt.core.logger import AEDTLogger
from aedt.domain.models.epic import Epic
from aedt.domain.models.story import Story


class EpicParser:
    """
    Parses BMAD Epic documents from markdown files with YAML frontmatter.

    Handles Epic document parsing, metadata validation, and error recovery.
    """

    def __init__(self, config_manager: ConfigManager, logger: AEDTLogger):
        """
        Initialize EpicParser.

        Args:
            config_manager: Configuration manager instance
            logger: AEDTLogger instance
        """
        self.config = config_manager
        self.aedt_logger = logger
        self.logger = logger.get_logger("epic_parser")

    def parse_epics(self, project_path: str) -> List[Epic]:
        """
        Parse all Epic documents in the project.

        Args:
            project_path: Project root directory path

        Returns:
            List of successfully parsed Epic objects
        """
        epic_docs_path = self.config.get('epic_docs_path', 'docs/epics/')
        epic_file_pattern = self.config.get('epic_file_pattern', 'epic-*.md')

        # Build full pattern path
        full_pattern = os.path.join(project_path, epic_docs_path, epic_file_pattern)

        self.logger.info(f"Parsing Epic documents from pattern: {full_pattern}")

        # Find all matching files
        epic_files = glob.glob(full_pattern)

        if not epic_files:
            self.logger.warning(f"No Epic files found matching pattern: {full_pattern}")
            return []

        self.logger.info(f"Found {len(epic_files)} Epic file(s)")

        # Parse each file
        epics = []
        success_count = 0
        failure_count = 0

        for file_path in epic_files:
            epic = self.parse_single_epic(file_path)
            if epic:
                epics.append(epic)
                success_count += 1
            else:
                failure_count += 1

        self.logger.info(
            f"Epic parsing completed: {success_count} successful, {failure_count} failed"
        )

        return epics

    def parse_single_epic(self, file_path: str) -> Optional[Epic]:
        """
        Parse a single Epic file.

        Args:
            file_path: Absolute path to Epic markdown file

        Returns:
            Epic object if successful, None otherwise
        """
        self.logger.debug(f"Parsing Epic file: {file_path}")

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter and content separately
            post = frontmatter.loads(content)
            metadata = dict(post.metadata)
            epic_content = post.content  # Markdown content without frontmatter

            # Validate metadata
            if not metadata:
                self.logger.warning(
                    f"Epic file {file_path} has invalid frontmatter. Skipping."
                )
                return None

            is_valid, error_msg = self._validate_metadata(metadata)
            if not is_valid:
                self.logger.warning(
                    f"Epic file {file_path} validation failed: {error_msg}"
                )
                return None

            epic_id = str(metadata['epic_id'])

            # Parse stories from Epic content
            stories = self.parse_stories(epic_content, epic_id)

            # Create Epic object
            epic = Epic(
                id=epic_id,
                title=metadata['title'],
                description=metadata.get('description', ''),
                depends_on=[str(dep) for dep in metadata.get('depends_on', [])],
                priority=metadata.get('priority', 'MEDIUM').upper(),
                execution_mode=metadata.get('execution_mode', 'auto'),
                story_concurrency=metadata.get('story_concurrency', 3),
                stories=stories,
            )

            # Validate Epic object
            is_valid, error_msg = epic.validate()
            if not is_valid:
                self.logger.warning(
                    f"Epic object validation failed for {file_path}: {error_msg}"
                )
                return None

            self.logger.info(
                f"Successfully parsed Epic {epic.id}: {epic.title}"
            )

            return epic

        except FileNotFoundError:
            self.logger.error(f"Epic file not found: {file_path}")
            return None
        except PermissionError:
            self.logger.error(f"Permission denied reading Epic file: {file_path}")
            return None
        except Exception as e:
            self.logger.error(
                f"Unexpected error parsing Epic file {file_path}: {str(e)}"
            )
            return None

    def _extract_yaml_frontmatter(self, content: str) -> Optional[dict]:
        """
        Extract and parse YAML frontmatter from markdown content.

        Args:
            content: Markdown file content

        Returns:
            Dictionary of metadata, or None if invalid
        """
        try:
            post = frontmatter.loads(content)
            return dict(post.metadata)
        except yaml.YAMLError as e:
            self.logger.debug(f"YAML parsing error: {str(e)}")
            return None
        except Exception as e:
            self.logger.debug(f"Frontmatter extraction error: {str(e)}")
            return None

    def _validate_metadata(self, metadata: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate Epic metadata contains required fields.

        Args:
            metadata: Dictionary of Epic metadata from frontmatter

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ['epic_id', 'title']
        for field in required_fields:
            if field not in metadata:
                return False, f"Missing required field: {field}"

        # Validate epic_id type
        if not isinstance(metadata['epic_id'], (int, str)):
            return False, "epic_id must be an integer or string"

        # Validate title type
        if not isinstance(metadata['title'], str):
            return False, "title must be a string"

        # Validate optional fields if present
        if 'depends_on' in metadata:
            if not isinstance(metadata['depends_on'], list):
                return False, "depends_on must be a list"

        if 'priority' in metadata:
            if metadata['priority'].upper() not in ['HIGH', 'MEDIUM', 'LOW']:
                return False, f"Invalid priority: {metadata['priority']}"

        if 'execution_mode' in metadata:
            if metadata['execution_mode'] not in ['single', 'multi', 'auto']:
                return False, f"Invalid execution_mode: {metadata['execution_mode']}"

        return True, None

    def parse_stories(self, epic_content: str, epic_id: str) -> List[Story]:
        """
        Parse Story list from Epic markdown content.

        Args:
            epic_content: Epic markdown content (without frontmatter)
            epic_id: Epic ID for validation and logging

        Returns:
            List of Story objects
        """
        self.logger.debug(f"Parsing stories from Epic {epic_id}")

        try:
            stories = []

            # Try numbered list format first
            stories_from_list = self._parse_stories_from_numbered_list(epic_content, epic_id)
            if stories_from_list:
                stories.extend(stories_from_list)

            # Try heading format if no numbered list found
            if not stories:
                stories_from_headings = self._parse_stories_from_headings(epic_content, epic_id)
                if stories_from_headings:
                    stories.extend(stories_from_headings)

            if not stories:
                self.logger.warning(f"Epic {epic_id} has no Stories defined")
                return []

            self.logger.info(f"Successfully parsed {len(stories)} stories from Epic {epic_id}")
            return stories

        except Exception as e:
            self.logger.error(f"Error parsing stories from Epic {epic_id}: {str(e)}")
            return []

    def _parse_stories_from_numbered_list(self, content: str, epic_id: str) -> List[Story]:
        """
        Parse stories from numbered list format.

        Format:
            ## Stories
            1. Story 3.1: Title
            2. Story 3.2: Another Title

        Args:
            content: Markdown content
            epic_id: Epic ID for validation

        Returns:
            List of Story objects
        """
        stories = []

        # Find Stories section
        stories_section_match = re.search(
            r'##\s+Stories\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not stories_section_match:
            return []

        stories_section = stories_section_match.group(1)

        # Match numbered list items: "1. Story X.Y: Title"
        story_pattern = re.compile(
            r'^\d+\.\s+Story\s+(\d+\.\d+):\s+(.+?)$',
            re.MULTILINE
        )

        for match in story_pattern.finditer(stories_section):
            story_id = match.group(1)
            story_title = match.group(2).strip()

            # Validate Story ID matches Epic ID
            if not story_id.startswith(epic_id + '.'):
                self.logger.warning(
                    f"Story ID {story_id} does not match Epic {epic_id}"
                )

            story = Story(
                id=story_id,
                title=story_title,
                description="",
                status="pending"
            )

            stories.append(story)

        return stories

    def _parse_stories_from_headings(self, content: str, epic_id: str) -> List[Story]:
        """
        Parse stories from heading format.

        Format:
            ### Story 3.1: Title
            Description...

            ### Story 3.2: Another Title
            Description...

        Args:
            content: Markdown content
            epic_id: Epic ID for validation

        Returns:
            List of Story objects
        """
        stories = []

        # Match h3 headings: "### Story X.Y: Title"
        story_pattern = re.compile(
            r'^###\s+Story\s+(\d+\.\d+):\s+(.+?)$',
            re.MULTILINE
        )

        matches = list(story_pattern.finditer(content))

        for i, match in enumerate(matches):
            story_id = match.group(1)
            story_title = match.group(2).strip()

            # Extract description (content until next story heading or end)
            start_pos = match.end()
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            description = content[start_pos:end_pos].strip()

            # Validate Story ID matches Epic ID
            if not story_id.startswith(epic_id + '.'):
                self.logger.warning(
                    f"Story ID {story_id} does not match Epic {epic_id}"
                )

            # Extract prerequisites if present
            prerequisites = self._extract_prerequisites(description)

            story = Story(
                id=story_id,
                title=story_title,
                description=description[:500],  # Limit description length
                prerequisites=prerequisites,
                status="pending"
            )

            stories.append(story)

        return stories

    def _extract_prerequisites(self, description: str) -> List[str]:
        """
        Extract prerequisites from Story description.

        Supports multiple formats:
        - YAML block: prerequisites: [3.1, 3.2]
        - Markdown list: - Story 3.1
        - Text reference: Requires Story 3.1

        Args:
            description: Story description text

        Returns:
            List of prerequisite Story IDs
        """
        prerequisites = []

        # Pattern 1: YAML format "prerequisites: [3.1, 3.2]"
        yaml_match = re.search(r'prerequisites:\s*\[([^\]]+)\]', description, re.IGNORECASE)
        if yaml_match:
            prereq_str = yaml_match.group(1)
            for item in prereq_str.split(','):
                item = item.strip().strip('"\'')
                if item and re.match(r'^\d+\.\d+$', item):
                    prerequisites.append(item)

        # Pattern 2: Markdown list "- Story 3.1" or "- 3.1"
        list_matches = re.findall(
            r'^\s*[-*]\s+(?:Story\s+)?(\d+\.\d+)',
            description,
            re.MULTILINE
        )
        prerequisites.extend(list_matches)

        # Pattern 3: Text reference "Requires Story 3.1" or "Depends on 3.1"
        # Also match multiple Story IDs in one sentence like "Requires Story 3.1 and Story 3.2"
        # Find all lines containing requirement keywords
        requirement_lines = re.finditer(
            r'^.*(?:Requires?|Depends?\s+on|After).*$',
            description,
            re.MULTILINE | re.IGNORECASE
        )
        for match in requirement_lines:
            line = match.group(0)
            # Extract all Story IDs from this line (X.Y format)
            story_ids = re.findall(r'\b(\d+\.\d+)\b', line)
            # Filter out any matches that aren't Story IDs (e.g., version numbers)
            # Story IDs in prerequisites context are typically single or double digit
            valid_story_ids = [sid for sid in story_ids if re.match(r'^\d{1,2}\.\d{1,2}$', sid)]
            prerequisites.extend(valid_story_ids)

        # Remove duplicates and sort
        prerequisites = sorted(set(prerequisites))

        return prerequisites
