"""
FastAPI server for JD Automation System.

Exposes idea enhancement, PRD generation, GitHub, and other services to the web UI.
"""

import os
import sys
import json
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

app = FastAPI(title="JD Automation API", version="2.0.0")

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


class PushFilesRequest(BaseModel):
    token: str
    repo_full_name: str
    files: dict  # {"path": "content", ...}
    commit_message: str = "Initial commit from JD Automation"


class EnhanceIdeaRequest(BaseModel):
    gemini_key: str
    app_idea: str
    tech_preferences: Optional[str] = None


class EnhanceIdeaResponse(BaseModel):
    success: bool
    enhanced_idea: Optional[dict] = None
    message: Optional[str] = None


class GeneratePRDRequest(BaseModel):
    gemini_key: str
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


@app.post("/api/enhance-idea", response_model=EnhanceIdeaResponse)
async def enhance_idea(request: EnhanceIdeaRequest):
    """Enhance a raw application idea using Gemini AI."""
    if not GEMINI_AVAILABLE:
        return EnhanceIdeaResponse(
            success=False,
            message="Gemini library not installed. Run: pip install google-generativeai"
        )

    try:
        genai.configure(api_key=request.gemini_key)
        model = genai.GenerativeModel('gemini-pro')

        prompt = build_enhance_idea_prompt(request.app_idea, request.tech_preferences)
        response = model.generate_content(prompt)
        text = response.text

        enhanced = parse_json_response(text)
        if enhanced and "title" in enhanced:
            return EnhanceIdeaResponse(success=True, enhanced_idea=enhanced)

        # Fallback: build structured response from raw text
        return EnhanceIdeaResponse(
            success=True,
            enhanced_idea=build_fallback_enhanced_idea(request.app_idea, request.tech_preferences)
        )

    except Exception as e:
        return EnhanceIdeaResponse(success=False, message=str(e))


@app.post("/api/generate-prd", response_model=GeneratePRDResponse)
async def generate_prd(request: GeneratePRDRequest):
    """Generate a comprehensive PRD with epics, user stories, and features."""
    if not GEMINI_AVAILABLE:
        return GeneratePRDResponse(
            success=False,
            message="Gemini library not installed. Run: pip install google-generativeai"
        )

    try:
        genai.configure(api_key=request.gemini_key)
        model = genai.GenerativeModel('gemini-pro')

        prompt = build_prd_prompt(request.enhanced_idea)
        response = model.generate_content(prompt)
        text = response.text

        prd_data = parse_json_response(text)
        if prd_data and "epics" in prd_data:
            prd_markdown = prd_to_markdown(prd_data, request.enhanced_idea)
            return GeneratePRDResponse(success=True, prd=prd_data, prd_markdown=prd_markdown)

        # Fallback
        prd_data = build_fallback_prd(request.enhanced_idea)
        prd_markdown = text if len(text) > 200 else prd_to_markdown(prd_data, request.enhanced_idea)
        return GeneratePRDResponse(success=True, prd=prd_data, prd_markdown=prd_markdown)

    except Exception as e:
        return GeneratePRDResponse(success=False, message=str(e))


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


def parse_json_response(text: str) -> Optional[dict]:
    """Try to extract and parse JSON from a Gemini response."""
    import re
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    brace_start = text.find('{')
    brace_end = text.rfind('}')
    if brace_start != -1 and brace_end != -1:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    return None


def build_enhance_idea_prompt(app_idea: str, tech_preferences: Optional[str] = None) -> str:
    """Build prompt for idea enhancement."""
    tech_section = ""
    if tech_preferences:
        tech_section = f"\nThe user prefers these technologies: {tech_preferences}\nIncorporate them where appropriate.\n"

    return f"""You are a senior product strategist. Enhance this rough application idea into a clear product concept.

**User's idea:**
{app_idea}
{tech_section}

**Return ONLY valid JSON** with this structure:
{{
  "title": "Concise project name",
  "description": "2-3 paragraph detailed description",
  "target_users": "Primary user personas",
  "problem_statement": "The specific problem this solves",
  "key_value_props": ["Prop 1", "Prop 2", "Prop 3"],
  "suggested_tech_stack": {{
    "frontend": ["tech1"],
    "backend": ["tech1"],
    "database": ["tech1"],
    "infrastructure": ["tech1"]
  }}
}}

Be specific and practical."""


def build_prd_prompt(enhanced_idea: dict) -> str:
    """Build prompt for PRD generation."""
    return f"""You are a senior product manager creating a comprehensive PRD.

**Application:**
Title: {enhanced_idea.get('title', 'Untitled')}
Description: {enhanced_idea.get('description', '')}
Target Users: {enhanced_idea.get('target_users', '')}
Problem: {enhanced_idea.get('problem_statement', '')}
Tech Stack: {json.dumps(enhanced_idea.get('suggested_tech_stack', {{}}))}

**Return ONLY valid JSON** with this structure:
{{
  "product_overview": {{
    "vision": "Vision statement",
    "goals": ["Goal 1", "Goal 2"],
    "success_metrics": ["Metric 1"]
  }},
  "epics": [
    {{
      "name": "Epic Name",
      "description": "Epic description",
      "priority": "P0",
      "user_stories": [
        {{
          "title": "Story Title",
          "story": "As a [user], I want [feature] so that [benefit]",
          "acceptance_criteria": ["Criterion 1"],
          "features": [
            {{"name": "Feature", "description": "What to build", "complexity": "S"}}
          ]
        }}
      ]
    }}
  ],
  "technical_architecture": {{
    "overview": "Architecture description",
    "components": ["Component 1"],
    "data_model": [{{"entity": "Name", "fields": ["field: type"], "relationships": "desc"}}],
    "api_endpoints": [{{"method": "GET", "path": "/api/x", "description": "desc"}}]
  }},
  "non_functional_requirements": {{
    "performance": ["Req 1"],
    "security": ["Req 1"],
    "scalability": ["Req 1"]
  }},
  "implementation_roadmap": {{
    "mvp_scope": "MVP description",
    "phases": [{{"name": "Phase 1", "epics": ["Epic"], "description": "desc"}}]
  }}
}}

Create 4-6 epics with 3-5 user stories each. Be specific and technical."""


def build_fallback_enhanced_idea(app_idea: str, tech_preferences: Optional[str] = None) -> dict:
    """Fallback enhanced idea when Gemini parsing fails."""
    title = app_idea.strip().split('.')[0].split('\n')[0][:80]
    if len(title) < 5:
        title = "Application Project"

    tech_stack = {"frontend": ["React", "TypeScript"], "backend": ["Python", "FastAPI"],
                  "database": ["PostgreSQL"], "infrastructure": ["Docker"]}

    return {
        "title": title,
        "description": app_idea,
        "target_users": "End users who need the described functionality",
        "problem_statement": f"Users need: {app_idea[:200]}",
        "key_value_props": ["Solves the core need", "Modern architecture", "Production-ready"],
        "suggested_tech_stack": tech_stack
    }


def build_fallback_prd(enhanced_idea: dict) -> dict:
    """Fallback PRD when Gemini parsing fails."""
    title = enhanced_idea.get("title", "Application")
    return {
        "product_overview": {
            "vision": f"Build {title}",
            "goals": ["Deliver core functionality", "Clean codebase", "Good documentation"],
            "success_metrics": ["All features implemented", "App runs without errors"]
        },
        "epics": [
            {
                "name": "Project Foundation",
                "description": "Project structure and setup",
                "priority": "P0",
                "user_stories": [{
                    "title": "Project Setup",
                    "story": "As a developer, I want a structured project so I can develop efficiently",
                    "acceptance_criteria": ["Project structure follows best practices", "Dependencies installable"],
                    "features": [
                        {"name": "Scaffolding", "description": "Create project structure", "complexity": "S"}
                    ]
                }]
            },
            {
                "name": "Core Features",
                "description": "Primary application functionality",
                "priority": "P0",
                "user_stories": [{
                    "title": "Core Logic",
                    "story": "As a user, I want the main features so I can accomplish my goals",
                    "acceptance_criteria": ["Core functionality works", "Error handling in place"],
                    "features": [
                        {"name": "Business logic", "description": "Main application features", "complexity": "L"},
                        {"name": "UI", "description": "User-facing interface", "complexity": "M"}
                    ]
                }]
            },
            {
                "name": "Data Layer",
                "description": "Data storage and access",
                "priority": "P0",
                "user_stories": [{
                    "title": "Data Persistence",
                    "story": "As a user, I want data to persist so I can access it later",
                    "acceptance_criteria": ["Data stored reliably", "CRUD operations work"],
                    "features": [
                        {"name": "Database schema", "description": "Data models", "complexity": "M"},
                        {"name": "Data access", "description": "Repository pattern", "complexity": "M"}
                    ]
                }]
            },
            {
                "name": "Testing",
                "description": "Automated testing",
                "priority": "P1",
                "user_stories": [{
                    "title": "Automated Tests",
                    "story": "As a developer, I want tests so I can refactor safely",
                    "acceptance_criteria": ["Unit tests cover core logic", "Tests runnable with one command"],
                    "features": [
                        {"name": "Unit tests", "description": "Test core modules", "complexity": "M"}
                    ]
                }]
            }
        ],
        "technical_architecture": {
            "overview": f"Architecture for {title}",
            "components": ["Frontend", "Backend API", "Database"],
            "data_model": [],
            "api_endpoints": []
        },
        "non_functional_requirements": {
            "performance": ["Sub-2s response times"],
            "security": ["Input validation", "Secrets in env vars"],
            "scalability": ["Stateless design"]
        },
        "implementation_roadmap": {
            "mvp_scope": "Foundation + Core + Data",
            "phases": [
                {"name": "Phase 1: Foundation", "epics": ["Project Foundation"], "description": "Setup"},
                {"name": "Phase 2: Core", "epics": ["Core Features", "Data Layer"], "description": "Main features"},
                {"name": "Phase 3: Quality", "epics": ["Testing"], "description": "Tests and polish"}
            ]
        }
    }


def prd_to_markdown(prd: dict, enhanced_idea: dict) -> str:
    """Convert PRD data to Markdown."""
    lines = []
    title = enhanced_idea.get("title", "Application")
    lines.append(f"# Product Requirements Document: {title}\n")

    overview = prd.get("product_overview", {})
    lines.append("## Product Overview\n")
    lines.append(f"**Vision:** {overview.get('vision', '')}\n")

    if enhanced_idea.get("description"):
        lines.append(f"**Description:** {enhanced_idea['description']}\n")

    lines.append("### Goals")
    for g in overview.get("goals", []):
        lines.append(f"- {g}")
    lines.append("")

    lines.append("## Epics & User Stories\n")
    for i, epic in enumerate(prd.get("epics", []), 1):
        lines.append(f"### Epic {i}: {epic['name']} [{epic.get('priority', 'P1')}]")
        lines.append(f"_{epic.get('description', '')}_\n")
        for j, story in enumerate(epic.get("user_stories", []), 1):
            lines.append(f"#### Story {i}.{j}: {story['title']}")
            lines.append(f"> {story.get('story', '')}\n")
            lines.append("**Acceptance Criteria:**")
            for ac in story.get("acceptance_criteria", []):
                lines.append(f"- [ ] {ac}")
            lines.append("\n**Features:**")
            for f in story.get("features", []):
                lines.append(f"- `[{f.get('complexity','M')}]` **{f['name']}** — {f.get('description','')}")
            lines.append("")

    arch = prd.get("technical_architecture", {})
    if arch:
        lines.append("## Technical Architecture\n")
        lines.append(f"{arch.get('overview', '')}\n")

    lines.append("---\n*Generated by JD Automation System*")
    return "\n".join(lines)


if __name__ == "__main__":
    print("Starting JD Automation API Server...")
    print("API Docs: http://127.0.0.1:8000/docs")
    print("UI: http://127.0.0.1:8000/")
    uvicorn.run(app, host="127.0.0.1", port=8000)
