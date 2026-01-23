# Architecture Documentation

## System Overview

The JD Automation System is a **local-first** pipeline that transforms job descriptions into fully implemented software projects. It coordinates multiple AI services (Gemini, Claude Code) with version control (GitHub) and professional networking (LinkedIn) to create portfolio-ready projects.

## Design Principles

1. **Modularity**: Clear service boundaries, single responsibility
2. **Local Control**: All orchestration happens locally, cloud only for AI/APIs
3. **Transparency**: Comprehensive logging and artifact preservation
4. **Security**: Secrets managed locally, sandboxed execution
5. **Reproducibility**: Version-controlled outputs, deterministic pipeline

## Architecture Diagram

```
┌─────────────┐
│   User/CLI  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│         Orchestration Engine                │
│  (core/orchestrator.py)                     │
│  - Manages pipeline flow                    │
│  - Error handling & recovery                │
│  - Status tracking & logging                │
└─────────────────────────────────────────────┘
       │
       │ Invokes modules sequentially:
       │
       ├─► JD Analysis ────► Extract skills
       │   (modules/jd_analysis.py)
       │
       ├─► Ideation ───────► Generate project idea
       │   (modules/ideation.py)
       │
       ├─► GitHub Service ─► Create repository
       │   (modules/github_service.py)
       │
       ├─► Gemini Client ──► Generate specification
       │   (modules/gemini_client.py)
       │
       ├─► Antigravity ────► Autonomous coding
       │   (modules/antigravity_runner.py)
       │
       ├─► Artifact Mgr ───► Organize files
       │   (modules/artifact_manager.py)
       │
       ├─► GitHub Publish ─► Push to remote
       │   (modules/github_service.py)
       │
       └─► LinkedIn ───────► Post project
           (modules/linkedin_service.py)
```

## Module Descriptions

### Core Layer

#### Orchestrator (`core/orchestrator.py`)

**Purpose**: Main pipeline coordinator
**Responsibilities**:

- Sequential execution of all pipeline stages
- Status tracking and event emission
- Error handling and recovery
- Run history management
- Artifact coordination

**Key Methods**:

- `run(job_description, auto_confirm)`: Execute full pipeline
- `_update_status(status, message)`: Update and log status
- `_save_run_history()`: Persist run metadata

#### Config (`core/config.py`)

**Purpose**: Configuration and secrets management
**Responsibilities**:

- Load environment variables
- Secure credential storage (keyring + .env fallback)
- Configuration validation
- Directory structure setup

### Service Modules

#### JD Analysis (`modules/jd_analysis.py`)

**Input**: Raw job description text
**Output**: Structured skills list, requirements
**Method**: Keyword matching + pattern recognition
**Notes**: Can be enhanced with actual NLP/LLM

#### Ideation (`modules/ideation.py`)

**Input**: JD text, extracted skills
**Output**: Project idea (title, description, tech stack)
**Method**: Template matching with scoring algorithm
**Templates**: Categorized by domain (web, ML, cloud, mobile)

#### GitHub Service (`modules/github_service.py`)

**Input**: Project name, description
**Output**: Repository URL, local git setup
**Integration**: PyGithub library + git CLI
**Features**:

- Repo creation with conflict handling
- Local git initialization
- Authenticated push with token

#### Gemini Client (`modules/gemini_client.py`)

**Input**: JD, project idea, skills
**Output**: Comprehensive specification document
**Integration**: Google GenerativeAI SDK
**Model**: gemini-pro (or gemini-1.5-pro)
**Prompt**: Structured to produce detailed technical specs

#### Antigravity Runner (`modules/antigravity_runner.py`)

**Input**: Project path, specification
**Output**: Implemented code, plan, logs
**Integration**: Claude Code / Antigravity IDE
**Current State**: Simulated (creates placeholder structure)
**Future**: Direct integration with Antigravity CLI/API

#### Artifact Manager (`modules/artifact_manager.py`)

**Input**: Project directory
**Output**: Organized file structure
**Operations**:

- Create standard directories (docs/, src/, tests/, logs/)
- Move files to appropriate locations
- Clean up temporary files

#### LinkedIn Service (`modules/linkedin_service.py`)

**Input**: Project title, description, URL
**Output**: LinkedIn project entry
**Integration**: LinkedIn REST API
**Auth**: OAuth 2.0 access token
**Note**: Requires LinkedIn developer app approval

### Interface Layer

#### CLI (`cli/main.py`)

**Interface**: Command-line with Rich formatting
**Commands**:

- `run`: Execute pipeline
- `setup`: Configure API keys
- `history`: View past runs
**Features**: Progress bars, colored output, error display

## Data Flow

```
Job Description (text)
    ↓
Skills Extraction (list)
    ↓
Project Ideation (dict)
    ↓
GitHub Repo Creation (URL + local path)
    ↓
Specification Generation (Markdown doc)
    ↓
AI Implementation (source code + artifacts)
    ↓
Artifact Organization (structured repo)
    ↓
GitHub Publishing (git commit + push)
    ↓
LinkedIn Posting (API call)
    ↓
Run Summary (JSON metadata)
```

## Storage

### Local Files

- **Configuration**: `.env`, keyring
- **Projects**: `projects/<project-name>/`
- **Logs**: `logs/jd_automation_*.log`
- **History**: `data/runs.json`

### Remote

- **GitHub**: Code repository (private by default)
- **LinkedIn**: Profile project entry

## Security Model

1. **Credentials**: Stored in OS keyring or encrypted .env
2. **API Keys**: Never logged or committed to git
3. **Execution**: Local sandboxing (can use Docker)
4. **Repos**: Private by default
5. **Audit**: Full logging of all operations

## Error Handling

- Each module catches exceptions and logs
- Orchestrator handles failures gracefully
- Run state saved even on failure
- Resume capability (future enhancement)

## Extension Points

1. **New Project Templates**: Add to `ideation.py`
2. **Custom Analysis**: Enhance `jd_analysis.py` with LLM
3. **Additional Integrations**: New modules (e.g., GitLab, Bitbucket)
4. **UI**: Web interface or desktop app
5. **Async Execution**: Make pipeline event-driven

## Performance Considerations

- **Bottlenecks**:
  - Gemini spec generation (30-60s)
  - Claude Code implementation (varies by complexity)
- **Optimization**:
  - Cache templates and common specs
  - Parallel independent operations
  - Stream LLM responses for real-time feedback

## Testing Strategy

- **Unit Tests**: Each module independently
- **Integration Tests**: Full pipeline with mocks
- **E2E Tests**: Actual API calls (rate-limited)
- **Fixtures**: Sample JDs for consistent testing

## Future Enhancements

1. **Web UI**: Dashboard for monitoring and management
2. **Multi-JD Batch Processing**: Process multiple JDs
3. **Template Customization**: User-defined project templates
4. **Analytics**: Success metrics, time tracking
5. **Collaboration**: Share runs and artifacts
6. **Real Antigravity Integration**: When API is available
