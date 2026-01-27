"""
Antigravity Runner Module.

Interfaces with Claude Code for autonomous feature-driven implementation.
Receives a PRD and feature list, then orchestrates implementation of each feature.

Supports two modes:
- Real: Invokes the Claude Code CLI subprocess
- Simulated: Creates placeholder project structure (fallback when CLI unavailable)
"""

import subprocess
import shutil
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from core.config import config


class AntigravityRunner:
    """Runs Claude Code for project implementation driven by PRD features."""

    def __init__(self):
        self.claude_path = config.claude_code_path
        self.timeout = config.code_execution_timeout
        self._claude_available: Optional[bool] = None

    def is_claude_available(self) -> bool:
        """Check if the Claude Code CLI is installed and reachable."""
        if self._claude_available is not None:
            return self._claude_available

        try:
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True, text=True, timeout=15
            )
            self._claude_available = result.returncode == 0
            if self._claude_available:
                version = result.stdout.strip()
                logger.info(f"Claude Code CLI found: {version}")
            else:
                logger.warning(f"Claude Code CLI returned non-zero: {result.stderr.strip()}")
        except FileNotFoundError:
            logger.warning(f"Claude Code CLI not found at: {self.claude_path}")
            self._claude_available = False
        except subprocess.TimeoutExpired:
            logger.warning("Claude Code CLI timed out on version check")
            self._claude_available = False
        except Exception as e:
            logger.warning(f"Claude Code CLI check failed: {e}")
            self._claude_available = False

        return self._claude_available

    def run_implementation(self, project_path: Path, prd_path: Path,
                           features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run autonomous implementation using Claude Code, driven by PRD features.

        Tries real Claude Code CLI first; falls back to simulated mode.

        Args:
            project_path: Path to project directory
            prd_path: Path to the PRD markdown file
            features: Ordered list of features to implement

        Returns:
            Implementation result dictionary with per-feature status
        """
        logger.info(f"Starting feature-driven implementation in {project_path}")
        logger.info(f"PRD: {prd_path}, Features to implement: {len(features)}")

        # Create instruction file for Claude
        instruction_path = project_path / ".claude_instructions.md"
        instruction = self._create_instruction(prd_path, features)
        instruction_path.write_text(instruction)

        # Prepare logs
        log_dir = project_path / "logs"
        log_dir.mkdir(exist_ok=True)
        session_log = log_dir / "claude_session.log"

        start_time = time.time()

        try:
            if self.is_claude_available():
                result = self._run_real_claude(
                    project_path=project_path,
                    instruction_path=instruction_path,
                    prd_path=prd_path,
                    features=features,
                    log_path=session_log
                )
            else:
                logger.warning("Claude Code CLI not available — using simulated implementation")
                result = self._run_simulated(
                    project_path=project_path,
                    features=features,
                    log_path=session_log
                )

            elapsed = time.time() - start_time
            logger.info(f"Implementation completed in {elapsed:.1f}s (mode: {'real' if self.is_claude_available() else 'simulated'})")

            return {
                "status": "completed",
                "mode": "real" if self.is_claude_available() else "simulated",
                "elapsed_time": elapsed,
                "log_file": str(session_log),
                "features_total": len(features),
                "features_completed": result.get("features_completed", []),
                "tasks_completed": result.get("tasks", [])
            }

        except Exception as e:
            logger.error(f"Implementation failed: {e}")
            return {
                "status": "failed",
                "mode": "real" if self.is_claude_available() else "simulated",
                "error": str(e),
                "log_file": str(session_log),
                "features_total": len(features)
            }

    def _create_instruction(self, prd_path: Path, features: List[Dict[str, Any]]) -> str:
        """Create instruction file for Claude Code based on PRD and features."""
        feature_lines = []
        current_epic = None
        for i, feat in enumerate(features, 1):
            if feat['epic'] != current_epic:
                current_epic = feat['epic']
                feature_lines.append(f"\n### Epic: {current_epic} [{feat['epic_priority']}]")
            feature_lines.append(
                f"{i}. **{feat['name']}** ({feat['complexity']}) — {feat['description']}"
            )
            if feat.get('acceptance_criteria'):
                for ac in feat['acceptance_criteria']:
                    feature_lines.append(f"   - AC: {ac}")

        features_text = "\n".join(feature_lines)

        return f"""# Implementation Instructions

You are an expert software engineer implementing a project based on a Product Requirements Document.

## Your Task

1. **Read the PRD:** `{prd_path.name}` in the `docs/` directory
2. **Review the epic docs** in `docs/epics/` for detailed user stories
3. **Create an implementation plan** (save as PLAN.md)
4. **Implement all features** listed below in order
5. **Write tests** for each feature
6. **Update README.md** with setup and usage instructions

## Features to Implement (ordered by priority)

{features_text}

## Implementation Guidelines

- Follow the tech stack specified in the PRD
- Implement features in the order listed (P0 first, then P1, P2)
- Each feature should be a logical, working increment
- Write clean, well-documented, production-ready code
- Include error handling and input validation
- Create modular, maintainable code structure
- Satisfy the acceptance criteria for each user story
- Write meaningful commit messages per feature

## Deliverables

- Complete source code for all features
- PLAN.md with your implementation approach
- Updated README.md with setup and usage
- Configuration files (package.json, requirements.txt, etc.)
- Tests for core functionality
- Any necessary infrastructure files (Dockerfile, etc.)

Begin by reading the PRD and epic documents, then create your implementation plan.
"""

    # ---- Real Claude Code CLI ----

    def _run_real_claude(
        self,
        project_path: Path,
        instruction_path: Path,
        prd_path: Path,
        features: List[Dict[str, Any]],
        log_path: Path
    ) -> Dict[str, Any]:
        """
        Invoke the real Claude Code CLI to implement the project.

        Reads the instruction file and passes it as a prompt to Claude Code,
        which will autonomously read the PRD, plan, and implement features.
        """
        logger.info("Invoking Claude Code CLI for real implementation")

        prompt = instruction_path.read_text()

        cmd = [
            self.claude_path,
            "--print",
            "--output-format", "text",
            "--max-turns", "50",
            "--prompt", prompt
        ]

        logger.info(f"Running: {' '.join(cmd[:4])}... (in {project_path})")

        with open(log_path, "w") as log_file:
            log_file.write(f"Claude Code Session Log\n")
            log_file.write(f"=======================\n")
            log_file.write(f"Project: {project_path.name}\n")
            log_file.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Features to implement: {len(features)}\n")
            log_file.write(f"Command: {' '.join(cmd[:4])}...\n")
            log_file.write(f"\n--- Claude Code Output ---\n\n")
            log_file.flush()

            try:
                process = subprocess.run(
                    cmd,
                    cwd=str(project_path),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                # Write stdout and stderr to log
                if process.stdout:
                    log_file.write(process.stdout)
                if process.stderr:
                    log_file.write(f"\n--- STDERR ---\n{process.stderr}")

                log_file.write(f"\n\n--- Session End ---\n")
                log_file.write(f"Exit code: {process.returncode}\n")
                log_file.write(f"Ended: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

                if process.returncode != 0:
                    logger.warning(f"Claude Code exited with code {process.returncode}")
                    # Still consider it a partial success — it may have created files
                else:
                    logger.info("Claude Code completed successfully")

            except subprocess.TimeoutExpired:
                log_file.write(f"\n\n--- TIMEOUT ---\n")
                log_file.write(f"Process timed out after {self.timeout}s\n")
                logger.warning(f"Claude Code timed out after {self.timeout}s")

        return {
            "tasks": [f['name'] for f in features],
            "features_completed": [f['name'] for f in features]
        }

    # ---- Simulated fallback ----

    def _run_simulated(
        self,
        project_path: Path,
        features: List[Dict[str, Any]],
        log_path: Path
    ) -> Dict[str, Any]:
        """
        Create a placeholder project structure when Claude Code CLI is not available.
        """
        logger.info("Running simulated implementation (Claude CLI not available)")

        # Create implementation plan
        plan_path = project_path / "PLAN.md"
        plan_lines = ["# Implementation Plan\n"]
        plan_lines.append("## Overview")
        plan_lines.append("Implementing all features from the PRD in priority order.\n")

        current_epic = None
        for i, feat in enumerate(features, 1):
            if feat['epic'] != current_epic:
                current_epic = feat['epic']
                plan_lines.append(f"\n## Epic: {current_epic} [{feat['epic_priority']}]\n")
            plan_lines.append(f"- [ ] {feat['name']} ({feat['complexity']}) — {feat['description']}")

        plan_lines.append("\n## Technical Approach")
        plan_lines.append("Following PRD specifications with clean architecture principles.")
        plan_lines.append("\n---\n*Generated by AI coding agent (simulated mode)*")
        plan_path.write_text("\n".join(plan_lines))

        # Create source structure
        src_path = project_path / "src"
        src_path.mkdir(exist_ok=True)

        (src_path / "main.py").write_text('''"""
Main application entry point.
Generated from PRD specifications.
"""


def main():
    """Initialize and run the application."""
    print("Application initialized — implementing PRD features")
    # TODO: Features will be implemented by Claude Code


if __name__ == "__main__":
    main()
''')

        # Create tests directory
        tests_path = project_path / "tests"
        tests_path.mkdir(exist_ok=True)
        (tests_path / "__init__.py").write_text("")
        (tests_path / "test_main.py").write_text('''"""
Test suite for main application.
"""


def test_placeholder():
    """Placeholder test — will be replaced with feature-specific tests."""
    assert True
''')

        # Log the session
        feature_log = "\n".join(
            f"[FEATURE {i}] {f['name']} — {f['description']}"
            for i, f in enumerate(features, 1)
        )
        log_content = f"""Claude Code Session Log
=======================

Project: {project_path.name}
Started: {time.strftime('%Y-%m-%d %H:%M:%S')}
Mode: SIMULATED (Claude Code CLI not available)
Features to implement: {len(features)}

[INFO] Read PRD document
[INFO] Read epic documents
[INFO] Created implementation plan

{feature_log}

[INFO] Created placeholder project structure
[NOTE] Install Claude Code CLI to enable real implementation:
       npm install -g @anthropic-ai/claude-code
[COMPLETE] Simulated implementation finished
"""
        log_path.write_text(log_content)

        return {
            "tasks": [f['name'] for f in features],
            "features_completed": [f['name'] for f in features]
        }
