"""
API integration tests using FastAPI TestClient.

Tests endpoint request/response contracts, validation,
authentication, and error handling.
"""

import os
from unittest.mock import MagicMock, patch

# Set environment variables before any imports so settings and DB use test values
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_api.db")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("CORS_ORIGINS", "*")

from fastapi.testclient import TestClient
from api.server import app, sanitize_repo_name

client = TestClient(app)


# ============ Health & Root ============

class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "gemini_available" in data
        assert "auth_configured" in data


# ============ Helper Function Tests ============

class TestSanitizeRepoName:
    def test_basic_name(self):
        assert sanitize_repo_name("My Project") == "my-project"

    def test_special_characters(self):
        assert sanitize_repo_name("Hello World! @#$%") == "hello-world"

    def test_consecutive_dashes(self):
        assert sanitize_repo_name("a---b") == "a-b"

    def test_empty_string(self):
        assert sanitize_repo_name("") == "generated-project"

    def test_long_name(self):
        result = sanitize_repo_name("a" * 200)
        assert len(result) <= 100

    def test_already_valid(self):
        assert sanitize_repo_name("my-valid-repo") == "my-valid-repo"


# ============ Enhance Idea Endpoint ============

class TestEnhanceIdeaEndpoint:
    @patch("api.server.GeminiClient")
    def test_enhance_idea_success(self, mock_gemini_cls):
        mock_client = MagicMock()
        mock_client.enhance_idea.return_value = {
            "title": "TestApp",
            "description": "A test application",
        }
        mock_gemini_cls.return_value = mock_client

        response = client.post("/api/enhance-idea", json={
            "gemini_key": "test-key",
            "app_idea": "A test app idea for remote teams",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["enhanced_idea"]["title"] == "TestApp"

    @patch("api.server.GeminiClient")
    def test_enhance_idea_with_tech_prefs(self, mock_gemini_cls):
        mock_client = MagicMock()
        mock_client.enhance_idea.return_value = {"title": "TestApp"}
        mock_gemini_cls.return_value = mock_client

        response = client.post("/api/enhance-idea", json={
            "gemini_key": "test-key",
            "app_idea": "A test app for remote teams",
            "tech_preferences": "React, Node.js",
        })
        assert response.status_code == 200
        mock_client.enhance_idea.assert_called_once_with(
            "A test app for remote teams", "React, Node.js"
        )

    @patch("api.server.GeminiClient")
    def test_enhance_idea_error(self, mock_gemini_cls):
        mock_gemini_cls.side_effect = Exception("API key invalid")

        response = client.post("/api/enhance-idea", json={
            "gemini_key": "bad-key",
            "app_idea": "A test app idea for remote teams",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "API key invalid" in data["message"]


# ============ Generate PRD Endpoint ============

class TestGeneratePRDEndpoint:
    @patch("api.server.GeminiClient")
    def test_generate_prd_success(self, mock_gemini_cls):
        mock_client = MagicMock()
        mock_client.generate_prd.return_value = {
            "prd": {"epics": [{"name": "Setup"}]},
            "prd_markdown": "# PRD\n\n## Setup"
        }
        mock_gemini_cls.return_value = mock_client

        response = client.post("/api/generate-prd", json={
            "gemini_key": "test-key",
            "enhanced_idea": {"title": "TestApp", "description": "A test app"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["prd"]["epics"]) == 1
        assert "PRD" in data["prd_markdown"]

    @patch("api.server.GeminiClient")
    def test_generate_prd_error(self, mock_gemini_cls):
        mock_client = MagicMock()
        mock_client.generate_prd.side_effect = Exception("Generation failed")
        mock_gemini_cls.return_value = mock_client

        response = client.post("/api/generate-prd", json={
            "gemini_key": "test-key",
            "enhanced_idea": {"title": "TestApp"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Generation failed" in data["message"]


# ============ Validate Token Endpoint ============

class TestValidateTokenEndpoint:
    @patch("api.server.Github")
    def test_valid_token(self, mock_github_cls):
        mock_user = MagicMock()
        mock_user.login = "testuser"
        mock_client = MagicMock()
        mock_client.get_user.return_value = mock_user
        mock_github_cls.return_value = mock_client

        response = client.post("/api/validate-token", json={"token": "ghp_testtoken"})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["username"] == "testuser"

    @patch("api.server.Github")
    def test_invalid_token(self, mock_github_cls):
        from github import GithubException
        mock_client = MagicMock()
        mock_client.get_user.side_effect = GithubException(401, "Bad credentials", None)
        mock_github_cls.return_value = mock_client

        response = client.post("/api/validate-token", json={"token": "bad-token"})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


# ============ Create Repo Endpoint ============

class TestCreateRepoEndpoint:
    @patch("api.server.repo_exists", return_value=False)
    @patch("api.server.Github")
    def test_create_repo_success(self, mock_github_cls, mock_exists):
        mock_repo = MagicMock()
        mock_repo.html_url = "https://github.com/user/test-project"
        mock_repo.clone_url = "https://github.com/user/test-project.git"
        mock_repo.full_name = "user/test-project"

        mock_user = MagicMock()
        mock_user.create_repo.return_value = mock_repo
        mock_client = MagicMock()
        mock_client.get_user.return_value = mock_user
        mock_github_cls.return_value = mock_client

        response = client.post("/api/create-repo", json={
            "token": "ghp_test",
            "name": "Test Project",
            "description": "A test project",
            "private": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["name"] == "test-project"
        assert data["url"] == "https://github.com/user/test-project"

    @patch("api.server.Github")
    def test_create_repo_github_error(self, mock_github_cls):
        from github import GithubException
        mock_client = MagicMock()
        mock_client.get_user.side_effect = GithubException(401, "Bad credentials", None)
        mock_github_cls.return_value = mock_client

        response = client.post("/api/create-repo", json={
            "token": "bad-token",
            "name": "Test Project",
        })
        assert response.status_code == 400


# ============ Run Endpoints ============

class TestStartRunEndpoint:
    def test_start_run_validation_short_idea(self):
        response = client.post("/api/run", json={
            "gemini_key": "key",
            "github_token": "token",
            "github_username": "user",
            "app_idea": "short",
        })
        assert response.status_code == 422  # Pydantic validation error

    @patch("api.server.Thread")
    def test_start_run_success(self, mock_thread_cls):
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        response = client.post("/api/run", json={
            "gemini_key": "key",
            "github_token": "token",
            "github_username": "user",
            "app_idea": "A comprehensive project management tool for remote teams with real-time collaboration",
        })
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "started"
        mock_thread.start.assert_called_once()

    def test_get_run_status_not_found(self):
        response = client.get("/api/run/nonexistent_run_id")
        assert response.status_code == 404

    def test_stream_run_not_found(self):
        response = client.get("/api/run/nonexistent_run_id/stream")
        assert response.status_code == 404


# ============ Auth Endpoints ============

class TestAuthEndpoints:
    @patch("api.server.get_github_authorize_url")
    def test_auth_github_redirect(self, mock_get_url):
        mock_get_url.return_value = "https://github.com/login/oauth/authorize?client_id=test"

        response = client.get("/api/auth/github")
        assert response.status_code == 200
        data = response.json()
        assert "authorize_url" in data
        assert "github.com" in data["authorize_url"]

    @patch("api.server.get_or_create_user")
    @patch("api.server.get_db")
    @patch("api.server.get_github_user")
    @patch("api.server.encrypt_token")
    @patch("api.server.create_jwt")
    @patch("api.server.exchange_code_for_token")
    def test_auth_callback_success(
        self, mock_exchange, mock_create_jwt, mock_encrypt,
        mock_get_user, mock_get_db, mock_get_or_create
    ):
        mock_exchange.return_value = "ghp_test_token"
        mock_get_user.return_value = {
            "id": 12345,
            "login": "testuser",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
            "email": "test@example.com",
        }

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.github_username = "testuser"
        mock_user.github_avatar_url = "https://avatars.githubusercontent.com/u/12345"
        mock_user.email = "test@example.com"
        mock_get_or_create.return_value = mock_user

        mock_create_jwt.return_value = "jwt.test.token"
        mock_encrypt.return_value = "encrypted_token"

        response = client.get("/api/auth/callback?code=test_auth_code")
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "jwt.test.token"
        assert data["user"]["username"] == "testuser"

    def test_auth_me_no_token(self):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_auth_me_invalid_token(self):
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid.jwt.token"
        })
        assert response.status_code == 401


# ============ Runs List Endpoint ============

class TestRunsListEndpoint:
    def test_list_runs_no_auth(self):
        response = client.get("/api/runs")
        assert response.status_code == 401


# ============ Push Files Endpoint ============

class TestPushFilesEndpoint:
    @patch("api.server.Github")
    def test_push_files_success(self, mock_github_cls):
        mock_repo = MagicMock()
        mock_repo.get_contents.side_effect = Exception("Not found")
        mock_repo.create_file.return_value = None

        mock_client = MagicMock()
        mock_client.get_repo.return_value = mock_repo
        mock_github_cls.return_value = mock_client

        response = client.post("/api/push-files", json={
            "token": "ghp_test",
            "repo_full_name": "user/test-repo",
            "files": {"README.md": "# Test"},
            "commit_message": "Add readme",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["files"]) == 1
        assert data["files"][0]["action"] == "created"
