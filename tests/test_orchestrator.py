"""
Tests for the Orchestrator module.

Tests feature extraction, topological sorting, input validation,
and retry logic.
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from core.orchestrator import (
    Orchestrator, RunStatus,
    validate_app_idea, validate_enhanced_idea, validate_prd,
    retry_with_backoff, InputValidationError
)


class TestInputValidation:
    def test_validate_app_idea_empty(self):
        with pytest.raises(InputValidationError, match="cannot be empty"):
            validate_app_idea("")

    def test_validate_app_idea_none(self):
        with pytest.raises(InputValidationError, match="cannot be empty"):
            validate_app_idea(None)

    def test_validate_app_idea_too_short(self):
        with pytest.raises(InputValidationError, match="too short"):
            validate_app_idea("short")

    def test_validate_app_idea_too_long(self):
        with pytest.raises(InputValidationError, match="too long"):
            validate_app_idea("x" * 5001)

    def test_validate_app_idea_valid(self):
        result = validate_app_idea("  A project management tool for remote teams with Kanban boards  ")
        assert result == "A project management tool for remote teams with Kanban boards"

    def test_validate_enhanced_idea_missing_title(self):
        with pytest.raises(InputValidationError, match="title"):
            validate_enhanced_idea({"description": "desc"})

    def test_validate_enhanced_idea_valid(self, sample_enhanced_idea):
        result = validate_enhanced_idea(sample_enhanced_idea)
        assert result["title"] == "TeamFlow"

    def test_validate_prd_no_epics(self):
        with pytest.raises(InputValidationError, match="no epics"):
            validate_prd({"epics": []})

    def test_validate_prd_missing_epic_name(self):
        with pytest.raises(InputValidationError, match="missing a name"):
            validate_prd({"epics": [{"user_stories": []}]})

    def test_validate_prd_valid(self, sample_prd):
        result = validate_prd(sample_prd)
        assert len(result["epics"]) == 3


class TestRetryWithBackoff:
    def test_succeeds_first_try(self):
        fn = MagicMock(return_value="ok")
        result = retry_with_backoff(fn, max_retries=3)
        assert result == "ok"
        fn.assert_called_once()

    def test_succeeds_after_retries(self):
        fn = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "ok"])
        result = retry_with_backoff(fn, max_retries=3, base_delay=0.01)
        assert result == "ok"
        assert fn.call_count == 3

    def test_exhausts_retries(self):
        fn = MagicMock(side_effect=Exception("always fails"))
        with pytest.raises(Exception, match="always fails"):
            retry_with_backoff(fn, max_retries=2, base_delay=0.01)
        assert fn.call_count == 2

    def test_calls_on_retry_callback(self):
        fn = MagicMock(side_effect=[Exception("fail"), "ok"])
        callback = MagicMock()
        retry_with_backoff(fn, max_retries=2, base_delay=0.01, on_retry=callback)
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == 1  # attempt number


class TestFeatureExtraction:
    def test_extract_features_basic(self, sample_prd):
        orch = Orchestrator.__new__(Orchestrator)
        features = orch._extract_features(sample_prd)
        assert len(features) == 4  # 1 + 2 + 1 features across 3 epics

    def test_extract_features_includes_metadata(self, sample_prd):
        orch = Orchestrator.__new__(Orchestrator)
        features = orch._extract_features(sample_prd)
        first = features[0]
        assert "epic" in first
        assert "epic_priority" in first
        assert "story" in first
        assert "name" in first
        assert "description" in first
        assert "complexity" in first
        assert "acceptance_criteria" in first

    def test_features_ordered_by_dependency(self, sample_prd):
        orch = Orchestrator.__new__(Orchestrator)
        features = orch._extract_features(sample_prd)
        # P0 epics with no deps should come first
        assert features[0]["epic"] == "Project Setup & Infrastructure"
        # Auth depends on Setup, so its features come after
        auth_indices = [i for i, f in enumerate(features) if f["epic"] == "Authentication"]
        setup_indices = [i for i, f in enumerate(features) if f["epic"] == "Project Setup & Infrastructure"]
        assert min(auth_indices) > max(setup_indices)

    def test_features_without_dependencies_use_priority(self):
        prd = {
            "epics": [
                {"name": "Low Priority", "priority": "P2", "user_stories": [
                    {"title": "S1", "features": [{"name": "F1", "description": "d", "complexity": "S"}],
                     "acceptance_criteria": []}
                ]},
                {"name": "High Priority", "priority": "P0", "user_stories": [
                    {"title": "S2", "features": [{"name": "F2", "description": "d", "complexity": "S"}],
                     "acceptance_criteria": []}
                ]}
            ]
        }
        orch = Orchestrator.__new__(Orchestrator)
        features = orch._extract_features(prd)
        assert features[0]["epic"] == "High Priority"


class TestTopologicalSort:
    def test_simple_dependency_chain(self):
        orch = Orchestrator.__new__(Orchestrator)
        features = [
            {"epic": "C", "epic_priority": "P2", "complexity": "S"},
            {"epic": "A", "epic_priority": "P0", "complexity": "S"},
            {"epic": "B", "epic_priority": "P1", "complexity": "S"},
        ]
        epic_deps = {"A": [], "B": ["A"], "C": ["B"]}
        result = orch._topological_sort_features(features, epic_deps)
        assert result is not None
        assert result[0]["epic"] == "A"
        assert result[1]["epic"] == "B"
        assert result[2]["epic"] == "C"

    def test_cycle_returns_none(self):
        orch = Orchestrator.__new__(Orchestrator)
        features = [
            {"epic": "A", "epic_priority": "P0", "complexity": "S"},
            {"epic": "B", "epic_priority": "P1", "complexity": "S"},
        ]
        epic_deps = {"A": ["B"], "B": ["A"]}
        result = orch._topological_sort_features(features, epic_deps)
        assert result is None

    def test_no_deps_returns_none(self):
        orch = Orchestrator.__new__(Orchestrator)
        features = [{"epic": "A", "epic_priority": "P0", "complexity": "S"}]
        epic_deps = {"A": []}
        result = orch._topological_sort_features(features, epic_deps)
        assert result is None


class TestRunStatus:
    def test_pipeline_order_defined(self):
        assert RunStatus.PIPELINE_ORDER[0] == RunStatus.ENHANCING_IDEA
        assert RunStatus.PIPELINE_ORDER[-1] == RunStatus.COMPLETED

    def test_transitions_defined(self):
        assert RunStatus.COMPLETED in RunStatus.TRANSITIONS
        assert RunStatus.TRANSITIONS[RunStatus.COMPLETED] == []
