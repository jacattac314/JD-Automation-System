"""
FastAPI server for JD Automation frontend.

Exposes GitHub, Gemini, and other services to the web UI.
"""

import os
import sys
import base64
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from github import Github, GithubException

# Optional: Gemini import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

app = FastAPI(title="JD Automation API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static UI files
UI_DIR = Path(__file__).parent.parent / "ui"
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


# ============ Request/Response Models ============

class CreateRepoRequest(BaseModel):
    token: str
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
    token: str


class ValidateTokenResponse(BaseModel):
    valid: bool
    username: Optional[str] = None
    message: Optional[str] = None


class GenerateSpecRequest(BaseModel):
    gemini_key: str
    job_description: str
    project_title: str
    project_description: str
    skills: List[str]


class GenerateSpecResponse(BaseModel):
    success: bool
    specification: Optional[str] = None
    message: Optional[str] = None


class PushFilesRequest(BaseModel):
    token: str
    repo_full_name: str
    files: dict  # {"path": "content", ...}
    commit_message: str = "Initial commit from JD Automation"


class AnalyzeJDRequest(BaseModel):
    gemini_key: Optional[str] = None
    job_description: str


class AnalyzeJDResponse(BaseModel):
    skills: List[str]
    experience_level: str
    suggested_project: Optional[dict] = None


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
        "gemini_available": GEMINI_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/validate-token", response_model=ValidateTokenResponse)
async def validate_token(request: ValidateTokenRequest):
    """Validate GitHub token and return username."""
    try:
        client = Github(request.token)
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
        client = Github(request.token)
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
        client = Github(request.token)
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


@app.post("/api/generate-spec", response_model=GenerateSpecResponse)
async def generate_specification(request: GenerateSpecRequest):
    """Generate project specification using Gemini AI."""
    if not GEMINI_AVAILABLE:
        return GenerateSpecResponse(
            success=False,
            message="Gemini library not installed. Run: pip install google-generativeai"
        )

    try:
        genai.configure(api_key=request.gemini_key)
        model = genai.GenerativeModel('gemini-pro')

        prompt = build_specification_prompt(
            request.job_description,
            request.project_title,
            request.project_description,
            request.skills
        )

        response = model.generate_content(prompt)
        specification = response.text

        return GenerateSpecResponse(success=True, specification=specification)

    except Exception as e:
        return GenerateSpecResponse(success=False, message=str(e))


@app.post("/api/analyze-jd", response_model=AnalyzeJDResponse)
async def analyze_job_description(request: AnalyzeJDRequest):
    """Analyze job description and extract skills."""
    jd = request.job_description.lower()

    # Tech keywords
    TECH_KEYWORDS = [
        "python", "javascript", "java", "c++", "c#", "go", "rust", "ruby", "php",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "sql", "postgresql", "mysql", "mongodb", "redis",
        "git", "ci/cd", "jenkins", "github actions",
        "machine learning", "deep learning", "ai", "nlp", "computer vision",
        "rest", "graphql", "microservices", "api",
        "agile", "scrum", "tdd", "unit testing", "typescript"
    ]

    skills = []
    for keyword in TECH_KEYWORDS:
        if keyword in jd:
            skills.append(proper_case(keyword))

    skills = sorted(list(set(skills)))

    # Determine experience level
    if any(term in jd for term in ["senior", "lead", "principal", "staff"]):
        experience_level = "senior"
    elif any(term in jd for term in ["mid-level", "intermediate", "3-5 years"]):
        experience_level = "mid"
    elif any(term in jd for term in ["junior", "entry", "0-2 years"]):
        experience_level = "junior"
    else:
        experience_level = "mid"

    # Suggest project based on skills
    suggested_project = suggest_project(skills)

    return AnalyzeJDResponse(
        skills=skills,
        experience_level=experience_level,
        suggested_project=suggested_project
    )


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


def proper_case(keyword: str) -> str:
    """Convert keyword to proper case."""
    casing = {
        "javascript": "JavaScript", "typescript": "TypeScript",
        "node.js": "Node.js", "postgresql": "PostgreSQL",
        "mysql": "MySQL", "mongodb": "MongoDB", "graphql": "GraphQL",
        "ci/cd": "CI/CD", "aws": "AWS", "gcp": "GCP",
        "api": "API", "nlp": "NLP", "ai": "AI", "tdd": "TDD"
    }
    return casing.get(keyword.lower(), keyword.title())


def suggest_project(skills: List[str]) -> dict:
    """Suggest a project based on skills."""
    skills_lower = [s.lower() for s in skills]

    ml_count = sum(1 for s in skills_lower if s in ["python", "machine learning", "deep learning", "ai", "nlp"])
    cloud_count = sum(1 for s in skills_lower if s in ["aws", "azure", "gcp", "docker", "kubernetes"])

    if ml_count >= 2:
        return {"title": "Predictive Analytics Dashboard", "description": "ML-powered analytics platform", "category": "data"}
    elif cloud_count >= 2:
        return {"title": "Multi-Cloud Infrastructure Manager", "description": "IaC solution for cloud resources", "category": "cloud"}
    else:
        return {"title": "Real-time Collaboration Platform", "description": "Full-stack web app with real-time features", "category": "web"}


def build_specification_prompt(jd: str, title: str, description: str, skills: List[str]) -> str:
    """Build prompt for Gemini specification generation."""
    return f"""You are a senior technical architect. Create a comprehensive application specification.

**Job Description:**
{jd[:1500]}

**Project:**
Title: {title}
Description: {description}

**Skills to Demonstrate:**
{', '.join(skills[:10])}

**Create a detailed specification including:**

1. **Executive Summary** - Project overview and objectives

2. **System Architecture** - Component diagram (describe textually), data flow

3. **Technical Stack** - Frontend, backend, database, deployment

4. **Core Features** - 5-8 features with user stories

5. **API Design** - Key endpoints and data models

6. **Implementation Plan**
   - Phase 1: Foundation (setup, structure)
   - Phase 2: Core Features
   - Phase 3: Testing & Deployment

7. **Security Considerations** - Auth, data protection

8. **Testing Strategy** - Unit, integration, E2E

Format as well-structured Markdown. Be specific and technical."""


if __name__ == "__main__":
    print("🚀 Starting JD Automation API Server...")
    print("📍 API Docs: http://127.0.0.1:8000/docs")
    print("🌐 UI: http://127.0.0.1:8000/")
    uvicorn.run(app, host="127.0.0.1", port=8000)
