"""
Shared test fixtures for JD Automation System tests.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def sample_app_idea():
    """A realistic app idea for testing."""
    return (
        "A project management tool for remote teams that integrates with Slack, "
        "supports Kanban boards, time tracking, and automated daily standups via "
        "AI summarization. Team leads can create projects, assign tasks with "
        "priorities and deadlines, and visualize progress through burndown charts."
    )


@pytest.fixture
def sample_enhanced_idea():
    """A sample enhanced idea dict as returned by GeminiClient.enhance_idea()."""
    return {
        "title": "TeamFlow",
        "description": "TeamFlow is a project management platform for remote teams...",
        "target_users": "Remote team leads and developers at companies with 10-100 employees",
        "problem_statement": "Remote teams lack integrated tools for task management and standups",
        "key_value_props": [
            "Reduce standup meeting time by 80% with AI summaries",
            "Unified task and time tracking in one tool",
            "Slack-native workflow integration"
        ],
        "suggested_tech_stack": {
            "frontend": ["Next.js 14", "TanStack Query"],
            "backend": ["FastAPI", "Celery"],
            "database": ["PostgreSQL"],
            "infrastructure": ["Docker", "GitHub Actions"]
        }
    }


@pytest.fixture
def sample_prd():
    """A sample PRD structure as returned by GeminiClient.generate_prd()."""
    return {
        "product_overview": {
            "vision": "Build TeamFlow to eliminate remote team coordination overhead",
            "goals": ["Reduce standup time", "Centralize task tracking"],
            "success_metrics": ["80% reduction in standup duration"]
        },
        "epics": [
            {
                "name": "Project Setup & Infrastructure",
                "description": "Initialize project structure",
                "priority": "P0",
                "depends_on": [],
                "user_stories": [
                    {
                        "title": "Project Initialization",
                        "story": "As a developer, I want a scaffolded project",
                        "acceptance_criteria": [
                            "Given a clean checkout, when I run install, then deps install"
                        ],
                        "features": [
                            {
                                "name": "Scaffold FastAPI project",
                                "description": "Create FastAPI project with src/, tests/, config/",
                                "complexity": "S",
                                "depends_on": []
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Authentication",
                "description": "User auth with JWT",
                "priority": "P0",
                "depends_on": ["Project Setup & Infrastructure"],
                "user_stories": [
                    {
                        "title": "User Registration",
                        "story": "As a new user, I want to create an account",
                        "acceptance_criteria": [
                            "Given valid email and password, when I register, then account is created"
                        ],
                        "features": [
                            {
                                "name": "Create registration endpoint",
                                "description": "POST /api/v1/auth/register",
                                "complexity": "M",
                                "depends_on": []
                            },
                            {
                                "name": "Create login endpoint",
                                "description": "POST /api/v1/auth/login with JWT",
                                "complexity": "M",
                                "depends_on": []
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Core Features",
                "description": "Task management and Kanban",
                "priority": "P1",
                "depends_on": ["Authentication"],
                "user_stories": [
                    {
                        "title": "Kanban Board",
                        "story": "As a user, I want to manage tasks on a Kanban board",
                        "acceptance_criteria": [
                            "Given tasks exist, when I view the board, then I see columns"
                        ],
                        "features": [
                            {
                                "name": "Build Kanban board UI",
                                "description": "Drag-and-drop Kanban board with columns",
                                "complexity": "L",
                                "depends_on": []
                            }
                        ]
                    }
                ]
            }
        ],
        "technical_architecture": {
            "overview": "FastAPI backend with Next.js frontend",
            "components": ["API Server", "Frontend", "Database"],
            "data_model": [
                {
                    "entity": "User",
                    "fields": ["id: UUID", "email: VARCHAR(255)", "password_hash: VARCHAR(255)"],
                    "relationships": "User has_many Tasks"
                }
            ],
            "api_endpoints": [
                {
                    "method": "POST",
                    "path": "/api/v1/auth/register",
                    "description": "Register new user"
                }
            ]
        },
        "non_functional_requirements": {
            "performance": ["API < 200ms p95"],
            "security": ["bcrypt passwords", "JWT auth"],
            "scalability": ["Stateless API"],
            "error_handling": ["Consistent JSON errors"]
        },
        "implementation_roadmap": {
            "mvp_scope": "Auth + Core Features",
            "phases": [
                {"name": "Phase 1", "epics": ["Project Setup & Infrastructure"], "description": "Foundation"}
            ]
        }
    }


@pytest.fixture
def mock_gemini_model():
    """A mocked Gemini generative model."""
    model = MagicMock()
    return model
