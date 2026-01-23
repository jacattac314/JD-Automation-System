"""
Main orchestration engine for JD Automation System.

Coordinates the entire pipeline from JD input to project publication.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
import json

from core.config import config
from modules.jd_analysis import JDAnalyzer
from modules.ideation import ProjectIdeation
from modules.github_service import GitHubService
from modules.gemini_client import GeminiClient
from modules.antigravity_runner import AntigravityRunner
from modules.artifact_manager import ArtifactManager
from modules.linkedin_service import LinkedInService


class RunStatus:
    """Track run status and progress."""
    EXTRACTING_SKILLS = "extracting_skills"
    IDEATING_PROJECT = "ideating_project"
    CREATING_REPO = "creating_repo"
    GENERATING_SPEC = "generating_spec"
    IMPLEMENTING = "implementing"
    ORGANIZING_ARTIFACTS = "organizing_artifacts"
    PUBLISHING_GITHUB = "publishing_github"
    PUBLISHING_LINKEDIN = "publishing_linkedin"
    COMPLETED = "completed"
    FAILED = "failed"


class Orchestrator:
    """Main orchestration engine."""
    
    def __init__(self):
        self.github = GitHubService()
        self.gemini = GeminiClient()
        self.analyzer = JDAnalyzer()
        self.ideation = ProjectIdeation()
        self.antigravity = AntigravityRunner()
        self.artifact_manager = ArtifactManager()
        self.linkedin = LinkedInService() if config.enable_linkedin else None
        
        self.run_id: Optional[str] = None
        self.status = RunStatus.EXTRACTING_SKILLS
        self.start_time: Optional[float] = None
        self.run_data: Dict[str, Any] = {}
        
    def run(self, job_description: str, auto_confirm: bool = True) -> Dict[str, Any]:
        """
        Execute the full pipeline.

        Args:
            job_description: The job description text
            auto_confirm: If True, skip manual confirmations

        Returns:
            Dictionary with run results

        Raises:
            ValueError: If job_description is empty or None
        """
        # Validate input
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty or None")

        self.start_time = time.time()
        self.run_id = f"run_{int(self.start_time)}"

        logger.info(f"Starting run {self.run_id}")
        
        try:
            # Step 1: Extract skills from JD
            self._update_status(RunStatus.EXTRACTING_SKILLS, "Analyzing job description...")
            skills = self.analyzer.extract_skills(job_description)
            logger.info(f"Extracted skills: {skills}")
            self.run_data['skills'] = skills
            
            # Step 2: Generate project idea
            self._update_status(RunStatus.IDEATING_PROJECT, "Generating project idea...")
            project_idea = self.ideation.generate_idea(job_description, skills)
            logger.info(f"Project idea: {project_idea['title']}")
            self.run_data['project_idea'] = project_idea
            
            # Manual confirmation if needed
            if not auto_confirm:
                if not self._confirm_idea(project_idea):
                    logger.info("User rejected idea, regenerating...")
                    project_idea = self.ideation.generate_idea(job_description, skills)
                    self.run_data['project_idea'] = project_idea
            
            # Step 3: Create GitHub repository
            self._update_status(RunStatus.CREATING_REPO, "Creating GitHub repository...")
            repo_info = self.github.create_repository(
                project_name=project_idea['title'],
                description=project_idea['description']
            )
            logger.info(f"Created repo: {repo_info['url']}")
            self.run_data['repo'] = repo_info
            
            # Initialize local repo
            local_path = config.project_storage / repo_info['name']
            local_path.mkdir(exist_ok=True)
            
            # Create initial files
            self._create_initial_files(local_path, job_description, project_idea)
            
            # Step 4: Generate specification with Gemini
            self._update_status(RunStatus.GENERATING_SPEC, "Generating specification with Gemini...")
            spec = self.gemini.generate_specification(
                job_description=job_description,
                project_idea=project_idea,
                skills=skills
            )
            spec_path = local_path / "docs" / "Specification.md"
            spec_path.parent.mkdir(exist_ok=True)
            spec_path.write_text(spec)
            logger.info(f"Specification saved to {spec_path}")
            self.run_data['spec_path'] = str(spec_path)
            
            # Step 5: Autonomous implementation with Claude Code
            self._update_status(RunStatus.IMPLEMENTING, "Implementing project with Claude Code...")
            implementation_result = self.antigravity.run_implementation(
                project_path=local_path,
                spec_path=spec_path
            )
            logger.info("Implementation completed")
            self.run_data['implementation'] = implementation_result
            
            # Step 6: Organize artifacts
            self._update_status(RunStatus.ORGANIZING_ARTIFACTS, "Organizing project artifacts...")
            self.artifact_manager.organize(local_path)
            
            # Step 7: Publish to GitHub
            self._update_status(RunStatus.PUBLISHING_GITHUB, "Publishing to GitHub...")
            self.github.publish_project(local_path, repo_info)
            
            # Step 8: LinkedIn integration (optional)
            if self.linkedin:
                self._update_status(RunStatus.PUBLISHING_LINKEDIN, "Creating LinkedIn project entry...")
                linkedin_result = self.linkedin.create_project(
                    title=project_idea['title'],
                    description=self._create_linkedin_description(job_description, project_idea, skills),
                    url=repo_info['url']
                )
                self.run_data['linkedin'] = linkedin_result
            
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
        # Could emit event here for UI updates
    
    def _confirm_idea(self, project_idea: Dict[str, Any]) -> bool:
        """Prompt user to confirm project idea."""
        # For CLI, could use input() here
        # For now, just return True
        return True
    
    def _create_initial_files(self, path: Path, jd: str, project_idea: Dict[str, Any]):
        """Create initial repository files."""
        # README
        readme = f"""# {project_idea['title']}

{project_idea['description']}

**Generated from Job Description Automation System**

## Overview
This project was automatically generated based on a job description to demonstrate relevant skills and capabilities.

## Skills Demonstrated
{', '.join(self.run_data.get('skills', []))}

---
*Auto-generated on {datetime.now().strftime('%Y-%m-%d')}*
"""
        (path / "README.md").write_text(readme)
        
        # JD.md
        (path / "JOB_DESCRIPTION.md").write_text(f"# Original Job Description\n\n{jd}")
        
        # requirements.json
        requirements = {
            "skills": self.run_data.get('skills', []),
            "project_idea": project_idea
        }
        (path / "requirements.json").write_text(json.dumps(requirements, indent=2))
    
    def _create_linkedin_description(self, jd: str, project_idea: Dict[str, Any], skills: list) -> str:
        """Create LinkedIn project description."""
        return f"""{project_idea['description']}

Built as an automated demonstration of skills from a {project_idea.get('role', 'Software Engineering')} job description.

Skills: {', '.join(skills[:5])}

This project showcases practical application of modern development practices and technologies."""
    
    def _save_run_history(self):
        """Save run to local history."""
        history_file = config.data_dir / "runs.json"
        
        # Load existing history
        if history_file.exists():
            history = json.loads(history_file.read_text())
        else:
            history = []
        
        # Add this run
        history.append({
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "status": self.run_data.get('status'),
            "project": self.run_data.get('project_idea', {}).get('title'),
            "repo_url": self.run_data.get('repo', {}).get('url'),
            "elapsed_time": self.run_data.get('elapsed_time')
        })
        
        # Save
        history_file.write_text(json.dumps(history, indent=2))
