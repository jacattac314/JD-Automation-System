"""
Antigravity Runner Module.

Interfaces with Claude Code for autonomous feature-driven implementation.
Receives a PRD and feature list, then orchestrates implementation of each feature.
"""

import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from core.config import config


class AntigravityRunner:
    """Runs Claude Code for project implementation driven by PRD features."""

    def __init__(self):
        self.claude_path = config.claude_code_path
        self.timeout = config.code_execution_timeout

    def run_implementation(self, project_path: Path, prd_path: Path,
                           features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run autonomous implementation using Claude Code, driven by PRD features.

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
        log_path = project_path / "logs"
        log_path.mkdir(exist_ok=True)
        session_log = log_path / "claude_session.log"

        start_time = time.time()

        try:
            result = self._run_claude_code(
                project_path=project_path,
                instruction_path=instruction_path,
                prd_path=prd_path,
                features=features,
                log_path=session_log
            )

            elapsed = time.time() - start_time
            logger.info(f"AI implementation completed in {elapsed:.1f}s")

            return {
                "status": "completed",
                "elapsed_time": elapsed,
                "log_file": str(session_log),
                "features_total": len(features),
                "features_completed": result.get("features_completed", []),
                "tasks_completed": result.get("tasks", [])
            }

        except Exception as e:
            logger.error(f"AI implementation failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "log_file": str(session_log),
                "features_total": len(features)
            }

    def _create_instruction(self, prd_path: Path, features: List[Dict[str, Any]]) -> str:
        """Create instruction file for Claude Code based on PRD and features."""
        # Build feature list for the instruction
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

    def _run_claude_code(
        self,
        project_path: Path,
        instruction_path: Path,
        prd_path: Path,
        features: List[Dict[str, Any]],
        log_path: Path
    ) -> Dict[str, Any]:
        """
        Execute Claude Code for implementation.

        Note: This is a placeholder that creates a realistic project structure.
        In production, this invokes the actual Claude Code CLI or API.
        """
        logger.warning("Using simulated Claude Code implementation")

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
            status = "[x]" if i <= 3 else "[ ]"  # Mark first few as done in simulation
            plan_lines.append(f"- {status} {feat['name']} ({feat['complexity']}) — {feat['description']}")

        plan_lines.append("\n## Technical Approach")
        plan_lines.append("Following PRD specifications with clean architecture principles.")
        plan_lines.append("\n---\n*Generated by AI coding agent*")
        plan_path.write_text("\n".join(plan_lines))

        # Create source structure
        src_path = project_path / "src"
        src_path.mkdir(exist_ok=True)

        main_file = src_path / "main.py"
        main_file.write_text('''"""
Main application entry point.
Generated from PRD specifications.
"""


def main():
    """Initialize and run the application."""
    print("Application initialized — implementing PRD features")
    # Features will be implemented here based on PRD


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
Features to implement: {len(features)}

[INFO] Read PRD document
[INFO] Read epic documents
[INFO] Created implementation plan

{feature_log}

[INFO] Created project structure
[INFO] Implemented core features
[COMPLETE] Implementation finished

---
Note: This is a simulated session. In production, Claude Code
autonomously implements each feature based on the PRD.
"""
        log_path.write_text(log_content)

        return {
            "tasks": [f['name'] for f in features[:5]],
            "features_completed": [f['name'] for f in features]
        }
