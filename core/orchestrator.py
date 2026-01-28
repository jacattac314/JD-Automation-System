"""
Main orchestration engine for JD Automation System.

Coordinates the pipeline from app idea input to project publication.
Flow: Idea -> AI Enhancement -> PRD Generation -> GitHub Repo -> Feature Implementation -> Publish

Includes retry logic with exponential backoff, input validation, and
a state machine for pipeline step management.
"""

import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from loguru import logger
import json

from core.config import config
from modules.github_service import GitHubService
from modules.gemini_client import GeminiClient
from modules.antigravity_runner import AntigravityRunner
from modules.artifact_manager import ArtifactManager


class RunStatus:
    """Pipeline step states."""
    PENDING = "pending"
    ENHANCING_IDEA = "enhancing_idea"
    GENERATING_PRD = "generating_prd"
    CREATING_REPO = "creating_repo"
    BREAKING_DOWN_FEATURES = "breaking_down_features"
    IMPLEMENTING = "implementing"
    ORGANIZING_ARTIFACTS = "organizing_artifacts"
    PUBLISHING_GITHUB = "publishing_github"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    PAUSED = "paused"

    # Valid state transitions
    TRANSITIONS = {
        PENDING: [ENHANCING_IDEA, FAILED],
        ENHANCING_IDEA: [GENERATING_PRD, RETRYING, FAILED],
        GENERATING_PRD: [CREATING_REPO, RETRYING, FAILED],
        CREATING_REPO: [BREAKING_DOWN_FEATURES, RETRYING, FAILED],
        BREAKING_DOWN_FEATURES: [IMPLEMENTING, FAILED],
        IMPLEMENTING: [ORGANIZING_ARTIFACTS, RETRYING, FAILED],
        ORGANIZING_ARTIFACTS: [PUBLISHING_GITHUB, FAILED],
        PUBLISHING_GITHUB: [COMPLETED, RETRYING, FAILED],
        RETRYING: [ENHANCING_IDEA, GENERATING_PRD, CREATING_REPO,
                   IMPLEMENTING, PUBLISHING_GITHUB, FAILED],
        FAILED: [PENDING],  # Allow restart from failed
        COMPLETED: [],
    }

    # Steps in pipeline order (for resume support)
    PIPELINE_ORDER = [
        ENHANCING_IDEA, GENERATING_PRD, CREATING_REPO,
        BREAKING_DOWN_FEATURES, IMPLEMENTING,
        ORGANIZING_ARTIFACTS, PUBLISHING_GITHUB, COMPLETED
    ]


class InputValidationError(ValueError):
    """Raised when pipeline input validation fails."""
    pass


def retry_with_backoff(
    fn: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
) -> Any:
    """Execute a function with exponential backoff retry.

    Args:
        fn: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exception types to retry on
        on_retry: Optional callback(attempt, exception, delay) called before each retry

    Returns:
        The return value of fn()

    Raises:
        The last exception if all retries are exhausted
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except retryable_exceptions as e:
            last_exception = e
            if attempt == max_retries:
                break
            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1), max_delay)
            logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
            if on_retry:
                on_retry(attempt, e, delay)
            time.sleep(delay)

    raise last_exception


def validate_app_idea(app_idea: str) -> str:
    """Validate and sanitize the application idea input.

    Returns:
        Cleaned app idea string

    Raises:
        InputValidationError: If validation fails
    """
    if not app_idea or not isinstance(app_idea, str):
        raise InputValidationError("Application idea cannot be empty or None")

    cleaned = app_idea.strip()

    if len(cleaned) < 20:
        raise InputValidationError(
            f"Application idea is too short ({len(cleaned)} chars). "
            "Please provide at least 20 characters describing your application."
        )

    if len(cleaned) > 5000:
        raise InputValidationError(
            f"Application idea is too long ({len(cleaned)} chars). "
            "Please keep it under 5000 characters."
        )

    return cleaned


def validate_enhanced_idea(enhanced_idea: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the structure of an enhanced idea before PRD generation.

    Raises:
        InputValidationError: If required fields are missing or invalid
    """
    required_fields = ['title', 'description']
    for field in required_fields:
        if not enhanced_idea.get(field):
            raise InputValidationError(f"Enhanced idea is missing required field: {field}")

    title = enhanced_idea['title']
    if len(title) < 2 or len(title) > 200:
        raise InputValidationError(f"Enhanced idea title has invalid length: {len(title)}")

    return enhanced_idea


def validate_prd(prd_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate PRD structure before feature extraction.

    Raises:
        InputValidationError: If the PRD structure is invalid
    """
    if not prd_data.get('epics'):
        raise InputValidationError("PRD has no epics — cannot proceed with implementation")

    for i, epic in enumerate(prd_data['epics']):
        if not epic.get('name'):
            raise InputValidationError(f"Epic {i + 1} is missing a name")
        if not epic.get('user_stories'):
            logger.warning(f"Epic '{epic['name']}' has no user stories — it will produce no features")

    return prd_data


class Orchestrator:
    """Main orchestration engine with retry logic and state management."""

    def __init__(self):
        self.github = GitHubService()
        self.gemini = GeminiClient()
        self.antigravity = AntigravityRunner()
        self.artifact_manager = ArtifactManager()

        self.run_id: Optional[str] = None
        self.status = RunStatus.PENDING
        self.start_time: Optional[float] = None
        self.run_data: Dict[str, Any] = {}
        self._status_callback: Optional[Callable] = None

    def on_status_change(self, callback: Callable):
        """Register a callback for status updates: callback(status, message)."""
        self._status_callback = callback

    def run(self, app_idea: str, tech_preferences: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the full pipeline with retry logic and validation.

        Args:
            app_idea: The user's application idea text (20-5000 chars)
            tech_preferences: Optional technology stack preferences

        Returns:
            Dictionary with run results

        Raises:
            InputValidationError: If input validation fails
            Exception: If pipeline fails after retries
        """
        # Validate input
        app_idea = validate_app_idea(app_idea)

        self.start_time = time.time()
        self.run_id = f"run_{int(self.start_time)}"

        logger.info(f"Starting run {self.run_id}")

        try:
            # Step 1: Enhance the idea with AI (with retry)
            self._update_status(RunStatus.ENHANCING_IDEA, "Enhancing application idea with AI...")
            enhanced_idea = retry_with_backoff(
                fn=lambda: self.gemini.enhance_idea(app_idea, tech_preferences),
                max_retries=3,
                on_retry=lambda a, e, d: self._update_status(
                    RunStatus.RETRYING, f"Retrying idea enhancement (attempt {a + 1})..."
                )
            )
            enhanced_idea = validate_enhanced_idea(enhanced_idea)
            logger.info(f"Enhanced idea: {enhanced_idea.get('title', 'Untitled')}")
            self.run_data['enhanced_idea'] = enhanced_idea
            self.run_data['original_idea'] = app_idea

            # Step 2: Generate comprehensive PRD (with retry)
            self._update_status(RunStatus.GENERATING_PRD, "Generating PRD with epics and user stories...")
            prd_result = retry_with_backoff(
                fn=lambda: self.gemini.generate_prd(enhanced_idea),
                max_retries=3,
                on_retry=lambda a, e, d: self._update_status(
                    RunStatus.RETRYING, f"Retrying PRD generation (attempt {a + 1})..."
                )
            )
            prd_data = prd_result['prd']
            prd_markdown = prd_result['prd_markdown']
            prd_data = validate_prd(prd_data)
            logger.info(f"PRD generated with {len(prd_data.get('epics', []))} epics")
            self.run_data['prd'] = prd_data
            self.run_data['prd_markdown'] = prd_markdown

            # Step 3: Create GitHub repository (with retry)
            self._update_status(RunStatus.CREATING_REPO, "Creating GitHub repository...")
            repo_info = retry_with_backoff(
                fn=lambda: self.github.create_repository(
                    project_name=enhanced_idea['title'],
                    description=enhanced_idea.get('description', '')[:200]
                ),
                max_retries=3,
                base_delay=2.0,
                on_retry=lambda a, e, d: self._update_status(
                    RunStatus.RETRYING, f"Retrying repo creation (attempt {a + 1})..."
                )
            )
            logger.info(f"Created repo: {repo_info['url']}")
            self.run_data['repo'] = repo_info

            # Initialize local repo and create initial files
            local_path = config.project_storage / repo_info['name']
            local_path.mkdir(exist_ok=True)
            self._create_initial_files(local_path, enhanced_idea, prd_data, prd_markdown)

            # Step 4: Break down features from PRD
            self._update_status(RunStatus.BREAKING_DOWN_FEATURES, "Extracting features from PRD...")
            features = self._extract_features(prd_data)
            logger.info(f"Extracted {len(features)} features across {len(prd_data.get('epics', []))} epics")
            self.run_data['features'] = features
            self.run_data['epics_count'] = len(prd_data.get('epics', []))
            self.run_data['features_count'] = len(features)

            if not features:
                logger.warning("No features extracted from PRD — skipping implementation")
                self._update_status(RunStatus.COMPLETED, "No features to implement")
                self.run_data['status'] = 'success'
                self.run_data['implementation'] = {"status": "skipped", "reason": "no features"}
            else:
                # Step 5: Autonomous implementation with Claude Code
                self._update_status(RunStatus.IMPLEMENTING, "Implementing features with Claude Code...")
                prd_path = local_path / "docs" / "PRD.md"
                implementation_result = self.antigravity.run_implementation(
                    project_path=local_path,
                    prd_path=prd_path,
                    features=features
                )
                logger.info("Implementation completed")
                self.run_data['implementation'] = implementation_result

            # Step 6: Organize artifacts
            self._update_status(RunStatus.ORGANIZING_ARTIFACTS, "Organizing project artifacts...")
            self.artifact_manager.organize(local_path)

            # Step 7: Publish to GitHub (with retry)
            self._update_status(RunStatus.PUBLISHING_GITHUB, "Publishing to GitHub...")
            retry_with_backoff(
                fn=lambda: self.github.publish_project(local_path, repo_info),
                max_retries=3,
                base_delay=2.0,
                on_retry=lambda a, e, d: self._update_status(
                    RunStatus.RETRYING, f"Retrying GitHub publish (attempt {a + 1})..."
                )
            )

            # Complete
            elapsed = time.time() - self.start_time
            self._update_status(RunStatus.COMPLETED, f"Run completed in {elapsed:.1f}s")

            self.run_data['status'] = 'success'
            self.run_data['elapsed_time'] = elapsed
            self.run_data['run_id'] = self.run_id

            # Save run history
            self._save_run_history()

            return self.run_data

        except InputValidationError:
            raise  # Don't wrap validation errors
        except Exception as e:
            logger.error(f"Run failed: {e}", exc_info=True)
            self._update_status(RunStatus.FAILED, f"Error: {str(e)}")
            self.run_data['status'] = 'failed'
            self.run_data['error'] = str(e)
            self._save_run_history()
            raise

    def _update_status(self, status: str, message: str):
        """Update run status and notify callback if registered."""
        self.status = status
        logger.info(f"[{status}] {message}")
        if self._status_callback:
            try:
                self._status_callback(status, message)
            except Exception as e:
                logger.warning(f"Status callback error: {e}")

    def _extract_features(self, prd: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract features from the PRD, ordered by dependency graph then priority.

        Uses topological sorting when dependency information is available,
        falling back to priority-based ordering otherwise.
        """
        features = []
        # Build epic dependency map for resolving feature ordering
        epic_deps = {}
        for epic in prd.get('epics', []):
            epic_name = epic.get('name', 'Unknown Epic')
            epic_deps[epic_name] = epic.get('depends_on', [])

        for epic in prd.get('epics', []):
            epic_name = epic.get('name', 'Unknown Epic')
            epic_priority = epic.get('priority', 'P1')
            for story in epic.get('user_stories', []):
                story_title = story.get('title', 'Unknown Story')
                for feat in story.get('features', []):
                    features.append({
                        'epic': epic_name,
                        'epic_priority': epic_priority,
                        'epic_depends_on': epic.get('depends_on', []),
                        'story': story_title,
                        'story_text': story.get('story', ''),
                        'name': feat.get('name', 'Feature'),
                        'description': feat.get('description', ''),
                        'complexity': feat.get('complexity', 'M'),
                        'acceptance_criteria': story.get('acceptance_criteria', []),
                        'depends_on': feat.get('depends_on', [])
                    })

        # Try topological sort by epic dependencies, fall back to priority sort
        ordered = self._topological_sort_features(features, epic_deps)
        if ordered is not None:
            logger.info(f"Features ordered by dependency graph ({len(ordered)} features)")
            return ordered

        # Fallback: sort by priority (P0 first)
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        features.sort(key=lambda f: priority_order.get(f['epic_priority'], 9))
        return features

    def _topological_sort_features(self, features: List[Dict[str, Any]],
                                     epic_deps: Dict[str, List[str]]) -> Optional[List[Dict[str, Any]]]:
        """Sort features respecting epic dependency ordering.

        Returns None if dependencies contain cycles or are invalid.
        Within each dependency tier, features are sorted by priority then complexity.
        """
        if not epic_deps or all(len(deps) == 0 for deps in epic_deps.values()):
            return None

        # Topological sort of epics using Kahn's algorithm
        epic_names = list(epic_deps.keys())
        in_degree = {name: 0 for name in epic_names}
        adjacency = {name: [] for name in epic_names}

        for epic, deps in epic_deps.items():
            for dep in deps:
                if dep in adjacency:
                    adjacency[dep].append(epic)
                    in_degree[epic] = in_degree.get(epic, 0) + 1

        queue = [e for e in epic_names if in_degree.get(e, 0) == 0]
        sorted_epics = []

        while queue:
            # Sort queue by priority for deterministic ordering within same tier
            queue.sort()
            current = queue.pop(0)
            sorted_epics.append(current)
            for neighbor in adjacency.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Cycle detected — fall back
        if len(sorted_epics) != len(epic_names):
            logger.warning("Cycle detected in epic dependencies, falling back to priority sort")
            return None

        # Build epic order map
        epic_order = {name: i for i, name in enumerate(sorted_epics)}

        # Sort features: first by epic dependency order, then by priority, then by complexity
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        complexity_order = {'S': 0, 'M': 1, 'L': 2}

        features.sort(key=lambda f: (
            epic_order.get(f['epic'], 99),
            priority_order.get(f['epic_priority'], 9),
            complexity_order.get(f['complexity'], 1)
        ))

        return features

    def _create_initial_files(self, path: Path, enhanced_idea: Dict[str, Any],
                               prd: Dict[str, Any], prd_markdown: str):
        """Create initial repository files."""
        title = enhanced_idea.get('title', 'Project')
        description = enhanced_idea.get('description', '')
        tech_stack = enhanced_idea.get('suggested_tech_stack', {})

        # README
        tech_lines = []
        for layer, techs in tech_stack.items():
            if layer == "notes":
                continue
            if isinstance(techs, list):
                tech_lines.append(f"- **{layer.title()}:** {', '.join(techs)}")
            else:
                tech_lines.append(f"- **{layer.title()}:** {techs}")
        tech_section = "\n".join(tech_lines) if tech_lines else "See PRD for details"

        readme = f"""# {title}

{description}

## Technology Stack
{tech_section}

## Project Structure
See `docs/PRD.md` for the full Product Requirements Document including epics, user stories, and features.

## Getting Started
_Setup instructions will be added during implementation._

---
*Generated on {datetime.now().strftime('%Y-%m-%d')} by JD Automation System*
"""
        (path / "README.md").write_text(readme)

        # PRD document
        docs_path = path / "docs"
        docs_path.mkdir(exist_ok=True)
        (docs_path / "PRD.md").write_text(prd_markdown)

        # Structured PRD as JSON for programmatic access
        (docs_path / "prd.json").write_text(json.dumps(prd, indent=2))

        # Enhanced idea metadata
        (path / "project.json").write_text(json.dumps({
            "title": title,
            "description": description,
            "target_users": enhanced_idea.get('target_users', ''),
            "problem_statement": enhanced_idea.get('problem_statement', ''),
            "key_value_props": enhanced_idea.get('key_value_props', []),
            "tech_stack": tech_stack,
            "epics_count": len(prd.get('epics', [])),
            "features_count": sum(
                len(feat)
                for epic in prd.get('epics', [])
                for story in epic.get('user_stories', [])
                for feat in [story.get('features', [])]
            )
        }, indent=2))

        # Create epic-level docs
        epics_path = docs_path / "epics"
        epics_path.mkdir(exist_ok=True)
        for i, epic in enumerate(prd.get('epics', []), 1):
            epic_filename = f"{i:02d}-{epic['name'].lower().replace(' ', '-')}.md"
            epic_content = f"# Epic {i}: {epic['name']}\n\n"
            epic_content += f"**Priority:** {epic.get('priority', 'P1')}\n\n"
            epic_content += f"{epic.get('description', '')}\n\n"
            epic_content += "## User Stories\n\n"
            for j, story in enumerate(epic.get('user_stories', []), 1):
                epic_content += f"### {j}. {story['title']}\n\n"
                epic_content += f"> {story.get('story', '')}\n\n"
                epic_content += "**Acceptance Criteria:**\n"
                for ac in story.get('acceptance_criteria', []):
                    epic_content += f"- [ ] {ac}\n"
                epic_content += "\n**Features:**\n"
                for feat in story.get('features', []):
                    epic_content += f"- `[{feat.get('complexity', 'M')}]` **{feat['name']}** — {feat.get('description', '')}\n"
                epic_content += "\n"
            (epics_path / epic_filename).write_text(epic_content)

    def _save_run_history(self):
        """Save run to local history."""
        history_file = config.data_dir / "runs.json"

        if history_file.exists():
            history = json.loads(history_file.read_text())
        else:
            history = []

        enhanced_idea = self.run_data.get('enhanced_idea', {})

        history.append({
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "status": self.run_data.get('status'),
            "project_title": enhanced_idea.get('title', 'Unknown'),
            "app_idea": self.run_data.get('original_idea', '')[:200],
            "epics_count": self.run_data.get('epics_count', 0),
            "features_count": self.run_data.get('features_count', 0),
            "repo_url": self.run_data.get('repo', {}).get('url'),
            "elapsed_time": self.run_data.get('elapsed_time')
        })

        history_file.write_text(json.dumps(history, indent=2))
