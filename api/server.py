"""
FastAPI server for JD Automation System.

Exposes idea enhancement, PRD generation, GitHub, pipeline execution,
and real-time progress streaming to the web UI.
"""

import sys
import json
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from threading import Thread

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
import uvicorn

from github import Github, GithubException
from modules.gemini_client import GeminiClient
from core.settings import settings
from core.database import init_db, get_db, get_or_create_user, save_run, get_user_runs, Run as RunModel
from core.auth import (
    get_github_authorize_url, exchange_code_for_token, get_github_user,
    create_jwt, encrypt_token, decrypt_token,
    require_auth, optional_auth
)

app = FastAPI(title="JD Automation API", version="2.0.0")

# ============ In-Memory Run State (for SSE streaming) ============

_active_runs: Dict[str, Dict[str, Any]] = {}
_run_events: Dict[str, asyncio.Queue] = {}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database on server startup."""
    init_db()

# Serve static UI files
UI_DIR = Path(__file__).parent.parent / "ui"
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


# ============ Request/Response Models ============

class CreateRepoRequest(BaseModel):
    token: Optional[str] = None
    name: str
    description: Optional[str] = ""
    private: bool = True


class CreateRepoResponse(BaseModel):
    success: bool
    name: str
    url: str
    clone_url: str
    full_name: str
    message: Optional[str] = None


class ValidateTokenRequest(BaseModel):
    token: Optional[str] = None


class ValidateTokenResponse(BaseModel):
    valid: bool
    username: Optional[str] = None
    message: Optional[str] = None


class PushFilesRequest(BaseModel):
    token: Optional[str] = None
    repo_full_name: str
    files: dict  # {"path": "content", ...}
    commit_message: str = "Initial commit from JD Automation"


class StartRunRequest(BaseModel):
    gemini_key: Optional[str] = None
    github_token: Optional[str] = None
    github_username: Optional[str] = None
    app_idea: str
    tech_preferences: Optional[str] = None
    private: bool = True

    @validator('app_idea')
    def validate_app_idea(cls, v):
        v = v.strip()
        if len(v) < 20:
            raise ValueError('App idea must be at least 20 characters')
        if len(v) > 5000:
            raise ValueError('App idea must be at most 5000 characters')
        return v


class EnhanceIdeaRequest(BaseModel):
    gemini_key: Optional[str] = None
    app_idea: str
    tech_preferences: Optional[str] = None


class EnhanceIdeaResponse(BaseModel):
    success: bool
    enhanced_idea: Optional[dict] = None
    message: Optional[str] = None


class GeneratePRDRequest(BaseModel):
    gemini_key: Optional[str] = None
    enhanced_idea: dict


class GeneratePRDResponse(BaseModel):
    success: bool
    prd: Optional[dict] = None
    prd_markdown: Optional[str] = None
    message: Optional[str] = None


# ============ Endpoints ============

@app.get("/")
async def root():
    """Serve the UI."""
    index_path = UI_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "JD Automation API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "gemini_available": True,
        "auth_configured": bool(settings.github_client_id),
        "timestamp": datetime.now().isoformat()
    }


# ============ Authentication Endpoints ============

@app.get("/api/auth/github")
async def auth_github_redirect(redirect_uri: str = "http://127.0.0.1:8000/api/auth/callback"):
    """Get the GitHub OAuth authorization URL."""
    url = get_github_authorize_url(redirect_uri)
    return {"authorize_url": url}


@app.get("/api/auth/callback")
async def auth_github_callback(code: str):
    """Handle GitHub OAuth callback — exchange code for token and create session."""
    # Exchange authorization code for GitHub access token
    github_token = exchange_code_for_token(code)

    # Fetch user profile from GitHub
    github_user = get_github_user(github_token)

    # Create or update user in database
    db = get_db()
    try:
        user = get_or_create_user(
            db=db,
            github_id=github_user["id"],
            github_username=github_user["login"],
            avatar_url=github_user.get("avatar_url"),
            email=github_user.get("email"),
        )

        # Encrypt and store GitHub token
        user.github_token_encrypted = encrypt_token(github_token)
        db.commit()

        # Issue JWT
        jwt_token = create_jwt(user.id, user.github_username)

        return {
            "token": jwt_token,
            "user": {
                "id": user.id,
                "username": user.github_username,
                "avatar_url": user.github_avatar_url,
                "email": user.email,
            }
        }
    finally:
        db.close()


@app.get("/api/auth/me")
async def get_current_user(token_data: dict = Depends(require_auth)):
    """Get the currently authenticated user's profile."""
    db = get_db()
    try:
        from core.database import User
        user = db.query(User).filter(User.id == int(token_data["sub"])).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "username": user.github_username,
            "avatar_url": user.github_avatar_url,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        }
    finally:
        db.close()


@app.get("/api/runs")
async def list_runs(token_data: dict = Depends(require_auth), limit: int = 50, offset: int = 0):
    """Get the authenticated user's run history from the database."""
    db = get_db()
    try:
        runs = get_user_runs(db, user_id=int(token_data["sub"]), limit=limit, offset=offset)
        return {
            "runs": [
                {
                    "run_id": r.run_id,
                    "status": r.status,
                    "project_title": r.project_title,
                    "app_idea": r.app_idea[:200] if r.app_idea else None,
                    "repo_url": r.repo_url,
                    "epics_count": r.epics_count,
                    "features_count": r.features_count,
                    "features_completed": r.features_completed,
                    "elapsed_time": r.elapsed_time,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in runs
            ]
        }
    finally:
        db.close()


@app.post("/api/validate-token", response_model=ValidateTokenResponse)
async def validate_token(request: ValidateTokenRequest):
    """Validate GitHub token and return username."""
    try:
        token = request.token or settings.github_token
        if not token:
             return ValidateTokenResponse(valid=False, message="No GitHub token provided or configured")
        client = Github(token)
        user = client.get_user()
        username = user.login
        return ValidateTokenResponse(valid=True, username=username)
    except GithubException as e:
        return ValidateTokenResponse(valid=False, message=str(e))
    except Exception as e:
        return ValidateTokenResponse(valid=False, message=str(e))


@app.post("/api/create-repo", response_model=CreateRepoResponse)
async def create_repo(request: CreateRepoRequest):
    """Create a new GitHub repository."""
    try:
        token = request.token or settings.github_token
        if not token:
             raise HTTPException(status_code=400, detail="No GitHub token provided or configured")
        client = Github(token)
        user = client.get_user()

        # Sanitize repo name
        repo_name = sanitize_repo_name(request.name)

        # Check if repo exists and append number if needed
        base_name = repo_name
        counter = 1
        while repo_exists(user, repo_name):
            repo_name = f"{base_name}-{counter}"
            counter += 1

        # Create the repository
        repo = user.create_repo(
            name=repo_name,
            description=request.description or "",
            private=request.private,
            auto_init=True  # Initialize with README
        )

        return CreateRepoResponse(
            success=True,
            name=repo_name,
            url=repo.html_url,
            clone_url=repo.clone_url,
            full_name=repo.full_name
        )

    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/push-files")
async def push_files(request: PushFilesRequest):
    """Push files to an existing GitHub repository."""
    try:
        token = request.token or settings.github_token
        if not token:
             raise HTTPException(status_code=400, detail="No GitHub token provided or configured")
        client = Github(token)
        repo = client.get_repo(request.repo_full_name)

        results = []
        for file_path, content in request.files.items():
            try:
                # Check if file exists
                try:
                    existing = repo.get_contents(file_path)
                    repo.update_file(
                        path=file_path,
                        message=request.commit_message,
                        content=content,
                        sha=existing.sha
                    )
                    results.append({"path": file_path, "action": "updated"})
                except:
                    repo.create_file(
                        path=file_path,
                        message=request.commit_message,
                        content=content
                    )
                    results.append({"path": file_path, "action": "created"})
            except Exception as e:
                results.append({"path": file_path, "action": "error", "error": str(e)})

        return {"success": True, "files": results}

    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enhance-idea", response_model=EnhanceIdeaResponse)
async def enhance_idea(request: EnhanceIdeaRequest):
    """Enhance a raw application idea using Gemini AI."""
    try:
        # Client handles fallback if key is invalid or API fails
        gemini_key = request.gemini_key or settings.gemini_api_key
        client = GeminiClient(api_key=gemini_key)
        enhanced = client.enhance_idea(request.app_idea, request.tech_preferences)
        return EnhanceIdeaResponse(success=True, enhanced_idea=enhanced)
    except Exception as e:
        return EnhanceIdeaResponse(success=False, message=str(e))


@app.post("/api/generate-prd", response_model=GeneratePRDResponse)
async def generate_prd(request: GeneratePRDRequest):
    """Generate a comprehensive PRD with epics, user stories, and features."""
    try:
        gemini_key = request.gemini_key or settings.gemini_api_key
        client = GeminiClient(api_key=gemini_key)
        result = client.generate_prd(request.enhanced_idea)
        return GeneratePRDResponse(
            success=True, 
            prd=result.get("prd"), 
            prd_markdown=result.get("prd_markdown")
        )
    except Exception as e:
        return GeneratePRDResponse(success=False, message=str(e))


# ============ Pipeline Run Endpoints ============

@app.post("/api/run")
async def start_run(request: StartRunRequest):
    """Start a full pipeline run (idea -> PRD -> repo -> implementation -> publish).

    Returns a run_id that can be used to stream progress via /api/run/{run_id}/stream.
    """
    run_id = f"run_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"

    # Initialize run state
    _active_runs[run_id] = {
        "status": "starting",
        "started_at": datetime.now().isoformat(),
        "app_idea": request.app_idea,
        "steps": {},
        "result": None,
        "error": None,
    }
    _run_events[run_id] = asyncio.Queue()

    # Run the pipeline in a background thread
    thread = Thread(
        target=_execute_pipeline,
        args=(run_id, request),
        daemon=True
    )
    thread.start()

    return {"run_id": run_id, "status": "started"}


@app.get("/api/run/{run_id}/stream")
async def stream_run_progress(run_id: str):
    """Stream real-time progress for a pipeline run using Server-Sent Events (SSE)."""
    if run_id not in _active_runs:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        queue = _run_events.get(run_id)
        if not queue:
            return

        # Send current state immediately
        yield f"data: {json.dumps(_active_runs[run_id], default=str)}\n\n"

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event, default=str)}\n\n"

                # Stop streaming when pipeline finishes
                if event.get("step") == "pipeline" and event.get("status") in ("completed", "failed"):
                    break
            except asyncio.TimeoutError:
                # Send keepalive
                yield f": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/run/{run_id}")
async def get_run_status(run_id: str):
    """Get current status of a pipeline run."""
    if run_id not in _active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    return _active_runs[run_id]


def _execute_pipeline(run_id: str, request: StartRunRequest):
    """Execute the full pipeline in a background thread."""
    from modules.gemini_client import GeminiClient
    from modules.antigravity_runner import AntigravityRunner
    from modules.artifact_manager import ArtifactManager
    from core.config import config
    import time

    run_state = _active_runs[run_id]
    event_queue = _run_events[run_id]

    def emit(step: str, status: str, detail: str = "", data: Any = None):
        run_state["status"] = status
        run_state["steps"][step] = {"status": status, "detail": detail}
        if data:
            run_state["steps"][step]["data"] = data
        event = {"run_id": run_id, "step": step, "status": status,
                 "detail": detail, "timestamp": datetime.now().isoformat()}
        if data:
            event["data"] = data
        # Put event on queue for SSE consumers
        try:
            event_queue.put_nowait(event)
        except Exception:
            pass

    try:
        # Step 1: Enhance idea
        emit("enhance_idea", "in_progress", "Enhancing application idea with AI...")
        gemini_key = request.gemini_key or settings.gemini_api_key
        gemini = GeminiClient(api_key=gemini_key)
        enhanced_idea = gemini.enhance_idea(request.app_idea, request.tech_preferences)
        emit("enhance_idea", "completed", f"Enhanced: {enhanced_idea.get('title', 'Untitled')}")
        run_state["enhanced_idea"] = enhanced_idea

        # Step 2: Generate PRD
        emit("generate_prd", "in_progress", "Generating PRD with epics and user stories...")
        prd_result = gemini.generate_prd(enhanced_idea)
        prd_data = prd_result["prd"]
        prd_markdown = prd_result["prd_markdown"]
        epics_count = len(prd_data.get("epics", []))
        emit("generate_prd", "completed", f"PRD generated with {epics_count} epics",
             data={"epics_count": epics_count, "prd_markdown": prd_markdown[:2000]})
        run_state["prd"] = prd_data

        # Step 3: Create GitHub repo
        emit("create_repo", "in_progress", "Creating GitHub repository...")
        try:
            token = request.github_token or settings.github_token
            if not token:
                 raise ValueError("No GitHub token configured")
            client = Github(token)
            user = client.get_user()
            repo_name = sanitize_repo_name(enhanced_idea.get("title", "project"))
            base_name = repo_name
            counter = 1
            while repo_exists(user, repo_name):
                repo_name = f"{base_name}-{counter}"
                counter += 1
            repo = user.create_repo(
                name=repo_name,
                description=enhanced_idea.get("description", "")[:200],
                private=request.private,
                auto_init=True
            )
            repo_info = {"name": repo_name, "url": repo.html_url,
                         "clone_url": repo.clone_url, "full_name": repo.full_name}
            emit("create_repo", "completed", f"Created: {repo.html_url}", data=repo_info)
        except Exception as e:
            emit("create_repo", "failed", f"GitHub repo creation failed: {e}")
            repo_info = {"name": sanitize_repo_name(enhanced_idea.get("title", "project")),
                         "url": None, "clone_url": None, "full_name": None}

        run_state["repo"] = repo_info

        # Step 4: Extract features
        emit("extract_features", "in_progress", "Breaking down features from PRD...")
        from core.orchestrator import Orchestrator
        orch = Orchestrator()
        features = orch._extract_features(prd_data)
        emit("extract_features", "completed", f"Extracted {len(features)} features",
             data={"features_count": len(features)})

        # Step 5: Create local project and run implementation
        emit("implement", "in_progress", "Implementing features with Claude Code...")
        local_path = config.project_storage / repo_info["name"]
        local_path.mkdir(parents=True, exist_ok=True)

        # Create initial files
        orch._create_initial_files(local_path, enhanced_idea, prd_data, prd_markdown)

        # Run implementation with progress callback
        runner = AntigravityRunner()

        def on_impl_progress(progress_data):
            emit("implement", "in_progress",
                 f"Feature {progress_data.get('current_feature_index', 0)}/{progress_data.get('total_features', 0)}: "
                 f"{progress_data.get('current_feature_name', '')}",
                 data=progress_data)

        prd_path = local_path / "docs" / "PRD.md"
        impl_result = runner.run_implementation(
            project_path=local_path,
            prd_path=prd_path,
            features=features,
            progress_callback=on_impl_progress
        )
        impl_status = "completed" if impl_result.get("status") == "completed" else "failed"
        emit("implement", impl_status,
             f"Implementation {impl_status}: {len(impl_result.get('features_completed', []))} features done",
             data={"mode": impl_result.get("mode", "unknown"),
                   "features_completed": impl_result.get("features_completed", []),
                   "features_failed": impl_result.get("features_failed", [])})

        # Step 6: Push to GitHub
        if repo_info.get("full_name"):
            emit("publish", "in_progress", "Publishing to GitHub...")
            try:
                gh_repo = client.get_repo(repo_info["full_name"])
                # Push PRD and project.json at minimum
                files_to_push = {
                    "docs/PRD.md": prd_markdown,
                    "project.json": json.dumps(run_state.get("enhanced_idea", {}), indent=2)
                }
                for file_path, content in files_to_push.items():
                    try:
                        existing = gh_repo.get_contents(file_path)
                        gh_repo.update_file(file_path, f"Update {file_path}", content, existing.sha)
                    except Exception:
                        gh_repo.create_file(file_path, f"Add {file_path}", content)
                emit("publish", "completed", f"Published to {repo_info['url']}")
            except Exception as e:
                emit("publish", "failed", f"Publish failed: {e}")
        else:
            emit("publish", "skipped", "No GitHub repo — skipping publish")

        # Final result
        run_state["result"] = {
            "project_title": enhanced_idea.get("title"),
            "repo_url": repo_info.get("url"),
            "epics_count": epics_count,
            "features_count": len(features),
            "features_completed": len(impl_result.get("features_completed", [])),
            "mode": impl_result.get("mode", "unknown"),
        }
        emit("pipeline", "completed", "Pipeline finished successfully")

    except Exception as e:
        run_state["error"] = str(e)
        emit("pipeline", "failed", f"Pipeline error: {e}")


# ============ Helper Functions ============

def sanitize_repo_name(name: str) -> str:
    """Sanitize project name to valid GitHub repo name."""
    import re
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    name = name[:100]
    return name or "generated-project"


def repo_exists(user, repo_name: str) -> bool:
    """Check if repository already exists."""
    try:
        user.get_repo(repo_name)
        return True
    except GithubException:
        return False


if __name__ == "__main__":
    print("Starting JD Automation API Server...")
    print("API Docs: http://127.0.0.1:8000/docs")
    print("UI: http://127.0.0.1:8000/")
    uvicorn.run(app, host="127.0.0.1", port=8000)
