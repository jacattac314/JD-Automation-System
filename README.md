# Local-First Job Description Automation System

An autonomous system that transforms job descriptions into fully implemented GitHub projects with minimal user intervention.

## 📥 Get the App

**Desktop Applications:**
- 🪟 **Windows:** Download installer or portable version
- 🍎 **macOS:** Download for Intel or Apple Silicon
- 🐧 **Linux:** AppImage, DEB, or RPM packages

**Mobile & Web:**
- 📱 **Progressive Web App:** Install on iOS, Android, or desktop browsers
- 🌐 Works offline with full app experience

See [BUILDING.md](BUILDING.md) for build instructions or [DISTRIBUTION.md](DISTRIBUTION.md) for deployment options.

## Overview

This system leverages AI (Google Gemini for specifications, Anthropic Claude Code for implementation) to:

1. Analyze job description requirements and extract key skills
2. Generate a relevant project idea
3. Create a GitHub repository
4. Generate a comprehensive technical specification
5. Autonomously implement the project using Claude Code
6. Publish results to GitHub and LinkedIn

## Architecture

The system follows a modular pipeline architecture:

- **Input Interface**: CLI and UI for job description input
- **JD Analysis**: Extracts skills and requirements
- **Project Ideation**: Generates project ideas based on JD
- **GitHub Integration**: Creates and manages repositories
- **Specification Generation**: Uses Gemini for detailed specs
- **Build Orchestration**: Coordinates Claude Code for implementation
- **Artifact Management**: Organizes project files
- **Publishing**: Pushes to GitHub and LinkedIn

## Installation

### Prerequisites

- Python 3.10+
- Node.js 16+ (for UI)
- Git
- API Keys:
  - Google Gemini API
  - GitHub Personal Access Token
  - Anthropic API key
  - LinkedIn OAuth token (optional)

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd Application\ Generator

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run CLI
python -m jd_automation --help

# Run UI (optional)
cd ui
npm install
npm start
```

## Usage

### Desktop App (Electron)

**After installing the desktop app:**
- Launch from Start Menu (Windows), Applications (macOS), or App Menu (Linux)
- App includes bundled Python runtime - no Python installation needed
- Auto-updates automatically

### One-Click Startup (Development)

```bash
python start.py
```

This single command:
- Checks dependencies
- Starts the Python backend
- Opens the UI in your browser
- Ready in seconds!

### CLI Mode

```bash
python -m jd_automation --jd "Your job description here"
```

### UI Mode (Manual)

```bash
python -m jd_automation ui
```

### Progressive Web App (Mobile)

1. Visit the app URL in your mobile browser
2. Tap "Install" when prompted
3. App installs to home screen
4. Works offline!

## Security

- All API keys stored locally (encrypted)
- Code execution sandboxed
- Private GitHub repos by default
- No data sent to cloud except AI API calls

## Project Structure

```
jd-automation/
├── cli/                 # CLI entry point
├── ui/                  # Electron/Web UI
├── core/                # Core orchestration logic
├── modules/             # Service modules
├── data/                # Local run history
└── logs/                # System logs
```

## License

MIT
