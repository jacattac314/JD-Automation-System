"""
Main orchestration engine for JD Automation System.

Coordinates the pipeline from app idea input to project publication.
New flow: Idea -> AI Enhancement -> PRD Generation -> GitHub Repo -> Feature Implementation -> Publish
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger
import json

from core.config import config
from modules.github_service import GitHubService
from modules.gemini_client import GeminiClient
from modules.antigravity_runner import AntigravityRunner
from modules.artifact_manager import ArtifactManager


class RunStatus:
    """Track run status and progress."""
    ENHANCING_IDEA = "enhancing_idea"
    GENERATING_PRD = "generating_prd"
    CREATING_REPO = "creating_repo"
    BREAKING_DOWN_FEATURES = "breaking_down_features"
    IMPLEMENTING = "implementing"
    ORGANIZING_ARTIFACTS = "organizing_artifacts"
    PUBLISHING_GITHUB = "publishing_github"
    COMPLETED = "completed"
    FAILED = "failed"


class Orchestrator:
    """Main orchestration engine."""

    def __init__(self):
        self.github = GitHubService()
        self.gemini = GeminiClient()
        self.antigravity = AntigravityRunner()
        self.artifact_manager = ArtifactManager()

        self.run_id: Optional[str] = None
        self.status = RunStatus.ENHANCING_IDEA
        self.start_time: Optional[float] = None
        self.run_data: Dict[str, Any] = {}

    def run(self, app_idea: str, tech_preferences: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the full pipeline.

        Args:
            app_idea: The user's application idea text
            tech_preferences: Optional technology stack preferences

        Returns:
            Dictionary with run results

        Raises:
            ValueError: If app_idea is empty or None
        """
        if not app_idea or not app_idea.strip():
            raise ValueError("Application idea cannot be empty or None")

        self.start_time = time.time()
        self.run_id = f"run_{int(self.start_time)}"

        logger.info(f"Starting run {self.run_id}")

        try:
            # Step 1: Enhance the idea with AI
            self._update_status(RunStatus.ENHANCING_IDEA, "Enhancing application idea with AI...")
            enhanced_idea = self.gemini.enhance_idea(app_idea, tech_preferences)
            logger.info(f"Enhanced idea: {enhanced_idea.get('title', 'Untitled')}")
            self.run_data['enhanced_idea'] = enhanced_idea
            self.run_data['original_idea'] = app_idea

            # Step 2: Generate comprehensive PRD
            self._update_status(RunStatus.GENERATING_PRD, "Generating PRD with epics and user stories...")
            prd_result = self.gemini.generate_prd(enhanced_idea)
            prd_data = prd_result['prd']
            prd_markdown = prd_result['prd_markdown']
            logger.info(f"PRD generated with {len(prd_data.get('epics', []))} epics")
            self.run_data['prd'] = prd_data
            self.run_data['prd_markdown'] = prd_markdown

            # Step 3: Create GitHub repository
            self._update_status(RunStatus.CREATING_REPO, "Creating GitHub repository...")
            repo_info = self.github.create_repository(
                project_name=enhanced_idea['title'],
                description=enhanced_idea.get('description', '')[:200]
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

            # Step 7: Publish to GitHub
            self._update_status(RunStatus.PUBLISHING_GITHUB, "Publishing to GitHub...")
            self.github.publish_project(local_path, repo_info)

            # Complete
            elapsed = time.time() - self.start_time
            self._update_status(RunStatus.COMPLETED, f"Run completed in {elapsed:.1f}s")

            self.run_data['status'] = 'success'
            self.run_data['elapsed_time'] = elapsed
            self.run_data['run_id'] = self.run_id

            # Save run history
            self._save_run_history()

            return self.run_data

        except Exception as e:
            logger.error(f"Run failed: {e}", exc_info=True)
            self._update_status(RunStatus.FAILED, f"Error: {str(e)}")
            self.run_data['status'] = 'failed'
            self.run_data['error'] = str(e)
            self._save_run_history()
            raise

    def _update_status(self, status: str, message: str):
        """Update run status."""
        self.status = status
        logger.info(f"[{status}] {message}")

    def _extract_features(self, prd: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract a flat list of features from the PRD structure, ordered by epic priority."""
        features = []
        for epic in prd.get('epics', []):
            epic_name = epic.get('name', 'Unknown Epic')
            epic_priority = epic.get('priority', 'P1')
            for story in epic.get('user_stories', []):
                story_title = story.get('title', 'Unknown Story')
                for feat in story.get('features', []):
                    features.append({
                        'epic': epic_name,
                        'epic_priority': epic_priority,
                        'story': story_title,
                        'story_text': story.get('story', ''),
                        'name': feat.get('name', 'Feature'),
                        'description': feat.get('description', ''),
                        'complexity': feat.get('complexity', 'M'),
                        'acceptance_criteria': story.get('acceptance_criteria', [])
                    })

        # Sort by priority (P0 first)
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        features.sort(key=lambda f: priority_order.get(f['epic_priority'], 9))

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
