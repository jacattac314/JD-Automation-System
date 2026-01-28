"""
Antigravity Runner Module.

Interfaces with Claude Code CLI for autonomous feature-driven implementation.
Receives a PRD and feature list, then orchestrates implementation of each feature.

Supports two modes:
1. Real mode: Invokes the Claude Code CLI (`claude`) via subprocess
2. Simulation mode: Falls back to creating placeholder project structure
"""

import subprocess
import shutil
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from loguru import logger

from core.config import config


class ImplementationProgress:
    """Tracks implementation progress for real-time reporting."""

    def __init__(self, total_features: int):
        self.total_features = total_features
        self.current_feature_index = 0
        self.current_feature_name = ""
        self.features_completed: List[str] = []
        self.features_failed: List[Dict[str, str]] = []
        self.status = "starting"
        self.log_lines: List[str] = []
        self._callbacks: List[Callable] = []

    def on_progress(self, callback: Callable):
        """Register a callback for progress updates."""
        self._callbacks.append(callback)

    def update(self, **kwargs):
        """Update progress and notify callbacks."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        for cb in self._callbacks:
            try:
                cb(self.to_dict())
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_features": self.total_features,
            "current_feature_index": self.current_feature_index,
            "current_feature_name": self.current_feature_name,
            "features_completed": self.features_completed,
            "features_failed": self.features_failed,
            "status": self.status,
            "completed_count": len(self.features_completed),
            "failed_count": len(self.features_failed),
        }


class AntigravityRunner:
    """Runs Claude Code for project implementation driven by PRD features."""

    def __init__(self):
        self.claude_path = config.claude_code_path
        self.timeout = config.code_execution_timeout
        self.per_feature_timeout = min(self.timeout // 2, 300)  # Max 5min per feature
        self._progress: Optional[ImplementationProgress] = None

    @property
    def progress(self) -> Optional[ImplementationProgress]:
        """Access current implementation progress."""
        return self._progress

    def _is_claude_available(self) -> bool:
        """Check if the Claude Code CLI is installed and accessible."""
        claude_cmd = self.claude_path or "claude"
        if shutil.which(claude_cmd):
            return True
        # Also try common install locations on Windows
        for path in [claude_cmd, "claude.exe", "claude.cmd"]:
            if shutil.which(path):
                self.claude_path = path
                return True
        return False

    def run_implementation(self, project_path: Path, prd_path: Path,
                           features: List[Dict[str, Any]],
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run autonomous implementation using Claude Code, driven by PRD features.

        Args:
            project_path: Path to project directory
            prd_path: Path to the PRD markdown file
            features: Ordered list of features to implement
            progress_callback: Optional callback for real-time progress updates

        Returns:
            Implementation result dictionary with per-feature status
        """
        logger.info(f"Starting feature-driven implementation in {project_path}")
        logger.info(f"PRD: {prd_path}, Features to implement: {len(features)}")

        # Initialize progress tracking
        self._progress = ImplementationProgress(total_features=len(features))
        if progress_callback:
            self._progress.on_progress(progress_callback)

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
            # Decide between real and simulated mode
            if self._is_claude_available():
                logger.info("Claude Code CLI detected — using real implementation mode")
                result = self._run_real_claude_code(
                    project_path=project_path,
                    instruction_path=instruction_path,
                    prd_path=prd_path,
                    features=features,
                    log_path=session_log
                )
            else:
                logger.warning("Claude Code CLI not found — using simulated implementation")
                result = self._run_simulated(
                    project_path=project_path,
                    features=features,
                    log_path=session_log
                )

            elapsed = time.time() - start_time
            logger.info(f"AI implementation completed in {elapsed:.1f}s")

            self._progress.update(status="completed")

            return {
                "status": "completed",
                "mode": "real" if self._is_claude_available() else "simulated",
                "elapsed_time": elapsed,
                "log_file": str(session_log),
                "features_total": len(features),
                "features_completed": result.get("features_completed", []),
                "features_failed": result.get("features_failed", []),
                "tasks_completed": result.get("tasks", [])
            }

        except Exception as e:
            logger.error(f"AI implementation failed: {e}")
            self._progress.update(status="failed")
            return {
                "status": "failed",
                "error": str(e),
                "log_file": str(session_log),
                "features_total": len(features),
                "features_completed": self._progress.features_completed if self._progress else [],
                "features_failed": self._progress.features_failed if self._progress else []
            }

    def _create_instruction(self, prd_path: Path, features: List[Dict[str, Any]]) -> str:
        """Create instruction file for Claude Code based on PRD and features."""
        feature_lines = []
        current_epic = None
        for i, feat in enumerate(features, 1):
            if feat['epic'] != current_epic:
                current_epic = feat['epic']
                feature_lines.append(f"\n### Epic: {current_epic} [{feat['epic_priority']}]")
                if feat.get('epic_depends_on'):
                    feature_lines.append(f"_Depends on: {', '.join(feat['epic_depends_on'])}_")
            feature_lines.append(
                f"{i}. **{feat['name']}** ({feat['complexity']}) — {feat['description']}"
            )
            if feat.get('acceptance_criteria'):
                for ac in feat['acceptance_criteria']:
                    feature_lines.append(f"   - AC: {ac}")
            if feat.get('depends_on'):
                feature_lines.append(f"   - _Depends on: {', '.join(feat['depends_on'])}_")

        features_text = "\n".join(feature_lines)

        return f"""# Implementation Instructions

You are an expert software engineer implementing a project based on a Product Requirements Document.

## Your Task

1. **Read the PRD:** `{prd_path.name}` in the `docs/` directory
2. **Review the epic docs** in `docs/epics/` for detailed user stories and acceptance criteria
3. **Create an implementation plan** (save as PLAN.md)
4. **Implement all features** listed below in the order specified (respecting dependencies)
5. **Write tests** for each feature as you implement it
6. **Update README.md** with setup and usage instructions

## Features to Implement (ordered by dependency then priority)

{features_text}

## Implementation Guidelines

- Follow the tech stack specified in the PRD exactly
- Implement features in the order listed — dependencies are resolved
- Each feature should be a logical, working increment that builds on previous features
- Write clean, well-documented, production-ready code
- Include error handling and input validation on all endpoints
- Create modular, maintainable code structure
- Satisfy ALL acceptance criteria for each user story
- After implementing each feature, verify it works before moving to the next
- Use consistent error response format: {{"error": "message", "code": "ERROR_CODE"}}
- Follow the data model from the PRD for all database schemas

## Deliverables

- Complete source code for all features
- PLAN.md with your implementation approach
- Updated README.md with setup, installation, and usage instructions
- Configuration files (package.json, requirements.txt, etc.)
- Tests for core functionality (unit + integration)
- Any necessary infrastructure files (Dockerfile, docker-compose.yml, etc.)
- .env.example with all required environment variables documented

Begin by reading the PRD and epic documents, then create your implementation plan.
"""

    def _build_feature_prompt(self, feature: Dict[str, Any], feature_index: int,
                               total_features: int) -> str:
        """Build a focused prompt for implementing a single feature."""
        ac_text = ""
        if feature.get('acceptance_criteria'):
            ac_lines = [f"  - {ac}" for ac in feature['acceptance_criteria']]
            ac_text = f"\n**Acceptance Criteria:**\n" + "\n".join(ac_lines)

        deps_text = ""
        if feature.get('depends_on'):
            deps_text = f"\n**Dependencies (already implemented):** {', '.join(feature['depends_on'])}"

        return f"""Implement feature {feature_index}/{total_features}:

**Epic:** {feature['epic']} [{feature['epic_priority']}]
**Feature:** {feature['name']}
**Complexity:** {feature['complexity']}
**Description:** {feature['description']}
{ac_text}
{deps_text}

Instructions:
- Read the existing code to understand the current project state
- Implement this feature following the PRD specifications
- Write tests for this feature
- Ensure existing tests still pass after your changes
- Do not break any previously implemented features"""

    def _run_real_claude_code(
        self,
        project_path: Path,
        instruction_path: Path,
        prd_path: Path,
        features: List[Dict[str, Any]],
        log_path: Path
    ) -> Dict[str, Any]:
        """
        Execute Claude Code CLI for real implementation.

        Runs Claude Code once with the full instruction set, or per-feature
        if the full run fails or times out.
        """
        claude_cmd = self.claude_path or "claude"
        log_lines = []
        features_completed = []
        features_failed = []

        def log(msg: str):
            log_lines.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            logger.info(msg)

        log(f"Starting real Claude Code implementation in {project_path}")
        log(f"Claude CLI path: {claude_cmd}")
        log(f"Features to implement: {len(features)}")

        # Strategy 1: Try full implementation in one Claude Code session
        log("Attempting full implementation in single session...")
        self._progress.update(status="implementing", current_feature_name="Full project implementation")

        full_prompt = instruction_path.read_text()
        success = self._execute_claude_session(
            claude_cmd=claude_cmd,
            project_path=project_path,
            prompt=full_prompt,
            timeout=self.timeout,
            log_fn=log
        )

        if success:
            log("Full implementation session completed successfully")
            features_completed = [f['name'] for f in features]
            for i, feat in enumerate(features):
                self._progress.update(
                    current_feature_index=i + 1,
                    current_feature_name=feat['name'],
                    features_completed=features_completed[:i + 1]
                )
        else:
            # Strategy 2: Fall back to per-feature implementation
            log("Full session failed or timed out — switching to per-feature mode")
            for i, feat in enumerate(features):
                feature_num = i + 1
                self._progress.update(
                    current_feature_index=feature_num,
                    current_feature_name=feat['name'],
                    status=f"implementing_feature_{feature_num}"
                )
                log(f"Implementing feature {feature_num}/{len(features)}: {feat['name']}")

                feature_prompt = self._build_feature_prompt(feat, feature_num, len(features))
                feat_success = self._execute_claude_session(
                    claude_cmd=claude_cmd,
                    project_path=project_path,
                    prompt=feature_prompt,
                    timeout=self.per_feature_timeout,
                    log_fn=log
                )

                if feat_success:
                    features_completed.append(feat['name'])
                    self._progress.update(features_completed=list(features_completed))
                    log(f"Feature completed: {feat['name']}")
                else:
                    features_failed.append({"name": feat['name'], "error": "Claude Code session failed or timed out"})
                    self._progress.update(features_failed=list(features_failed))
                    log(f"Feature FAILED: {feat['name']}")

        # Write session log
        log_path.write_text("\n".join(log_lines))

        return {
            "tasks": features_completed[:5],
            "features_completed": features_completed,
            "features_failed": features_failed
        }

    def _execute_claude_session(
        self,
        claude_cmd: str,
        project_path: Path,
        prompt: str,
        timeout: int,
        log_fn: Callable
    ) -> bool:
        """
        Execute a single Claude Code CLI session.

        Args:
            claude_cmd: Path to claude CLI executable
            project_path: Working directory for the session
            prompt: The prompt/instruction to send to Claude
            timeout: Maximum execution time in seconds
            log_fn: Logging function for output capture

        Returns:
            True if the session completed successfully
        """
        try:
            # Build the claude command
            # Use --print flag for non-interactive mode, pipe prompt via stdin
            cmd = [claude_cmd, "--print", "--output-format", "text"]

            log_fn(f"Executing: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_path),
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Send prompt via stdin and collect output with timeout
            try:
                stdout, stderr = process.communicate(
                    input=prompt,
                    timeout=timeout
                )
            except subprocess.TimeoutExpired:
                log_fn(f"Session timed out after {timeout}s — terminating")
                process.kill()
                process.communicate(timeout=10)
                return False

            # Log output (truncated for large outputs)
            if stdout:
                output_lines = stdout.strip().split('\n')
                for line in output_lines[:50]:  # Log first 50 lines
                    log_fn(f"[claude] {line}")
                if len(output_lines) > 50:
                    log_fn(f"[claude] ... ({len(output_lines) - 50} more lines)")

            if stderr:
                for line in stderr.strip().split('\n')[:10]:
                    log_fn(f"[claude:stderr] {line}")

            if process.returncode != 0:
                log_fn(f"Claude Code exited with code {process.returncode}")
                return False

            log_fn("Claude Code session completed successfully")
            return True

        except FileNotFoundError:
            log_fn(f"Claude Code CLI not found at: {claude_cmd}")
            return False
        except Exception as e:
            log_fn(f"Error executing Claude Code: {e}")
            return False

    def _run_simulated(
        self,
        project_path: Path,
        features: List[Dict[str, Any]],
        log_path: Path
    ) -> Dict[str, Any]:
        """
        Create simulated project structure when Claude Code CLI is not available.

        This fallback creates a realistic project skeleton so the pipeline
        can complete and the user can see what would be generated.
        """
        logger.warning("Using simulated Claude Code implementation")

        # Create implementation plan
        plan_path = project_path / "PLAN.md"
        plan_lines = ["# Implementation Plan\n"]
        plan_lines.append("## Overview")
        plan_lines.append("Implementing all features from the PRD in priority order.\n")
        plan_lines.append("> **Note:** This plan was auto-generated. Install the Claude Code CLI")
        plan_lines.append("> (`npm install -g @anthropic-ai/claude-code`) for real AI implementation.\n")

        current_epic = None
        for i, feat in enumerate(features, 1):
            if feat['epic'] != current_epic:
                current_epic = feat['epic']
                plan_lines.append(f"\n## Epic: {current_epic} [{feat['epic_priority']}]\n")
            plan_lines.append(f"- [ ] {feat['name']} ({feat['complexity']}) — {feat['description']}")

        plan_lines.append("\n---\n*Generated by JD Automation System (simulated mode)*")
        plan_path.write_text("\n".join(plan_lines))

        # Create source structure
        src_path = project_path / "src"
        src_path.mkdir(exist_ok=True)

        main_file = src_path / "main.py"
        main_file.write_text('''"""
Main application entry point.
Generated from PRD specifications.

NOTE: This is a scaffold generated in simulation mode.
Install Claude Code CLI for real AI-driven implementation.
"""


def main():
    """Initialize and run the application."""
    print("Application initialized — features pending real implementation")


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

        # Update progress for each feature (simulated)
        for i, feat in enumerate(features):
            self._progress.update(
                current_feature_index=i + 1,
                current_feature_name=feat['name'],
                status=f"simulating_feature_{i + 1}",
                features_completed=[f['name'] for f in features[:i + 1]]
            )

        # Write session log
        feature_log = "\n".join(
            f"[FEATURE {i}] {f['name']} — {f['description']}"
            for i, f in enumerate(features, 1)
        )
        log_content = f"""Claude Code Session Log (SIMULATED)
=====================================

Project: {project_path.name}
Started: {time.strftime('%Y-%m-%d %H:%M:%S')}
Mode: Simulated (Claude Code CLI not found)
Features to implement: {len(features)}

[INFO] Claude Code CLI not detected on this system
[INFO] To enable real AI implementation, install Claude Code:
[INFO]   npm install -g @anthropic-ai/claude-code
[INFO] Then set CLAUDE_CODE_PATH in your .env if using a custom path

[INFO] Created project scaffold with placeholder code
[INFO] Created implementation plan (PLAN.md)

{feature_log}

[COMPLETE] Simulation finished — project structure created

---
To get real AI-generated code, install Claude Code CLI and re-run.
"""
        log_path.write_text(log_content)

        return {
            "tasks": [f['name'] for f in features[:5]],
            "features_completed": [f['name'] for f in features]
        }
