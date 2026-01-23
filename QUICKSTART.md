# Quick Start Guide

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

1. **Configure API keys:**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual API keys
# OR use the setup wizard:
python -m cli.main setup
```

## Required API Keys

- **Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **GitHub Token**: Create a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope
- **Anthropic API**: Get from [Anthropic Console](https://console.anthropic.com/)
- **LinkedIn** (optional): Create a developer app at [LinkedIn Developers](https://www.linkedin.com/developers/)

## Usage

### Basic Usage

```bash
# Run with inline job description
python -m cli.main run --jd "Your job description here..."

# Run with JD from file
python -m cli.main run --jd-file examples/sample_jd.txt

# Skip LinkedIn integration
python -m cli.main run --jd-file examples/sample_jd.txt --no-linkedin
```

### View History

```bash
python -m cli.main history
```

### Configuration

```bash
python -m cli.main setup
```

## What It Does

1. **Analyzes** the job description to extract required skills
2. **Generates** a relevant project idea based on those skills
3. **Creates** a GitHub repository for the project
4. **Generates** a detailed specification using Gemini AI
5. **Implements** the project autonomously using Claude Code
6. **Organizes** all artifacts (code, docs, logs)
7. **Publishes** to GitHub
8. **Posts** to LinkedIn (optional)

## Output

Each run creates:

- A GitHub repository with complete project code
- Comprehensive documentation (README, Specification)
- Implementation plan
- Test files
- Logs of the AI's implementation process
- Run history for tracking

## Example

```bash
# Run with the sample job description
python -m cli.main run --jd-file examples/sample_jd.txt
```

This will:

- Extract skills like Python, React, PostgreSQL, AWS
- Propose a relevant project (e.g., "Real-time Collaboration Platform")
- Create a private GitHub repo
- Generate a detailed spec with Gemini
- Implement the project with Claude Code
- Push everything to GitHub
- Add to your LinkedIn profile

## Directory Structure

After a run, you'll find:

```
projects/
└── your-project-name/
    ├── README.md
    ├── JOB_DESCRIPTION.md
    ├── requirements.json
    ├── docs/
    │   ├── Specification.md
    │   └── PLAN.md
    ├── src/
    │   └── main.py
    ├── tests/
    └── logs/
        └── claude_session.log
```

## Troubleshooting

### "Configuration errors"

- Make sure all required API keys are set in `.env`
- Run `python -m cli.main setup` to configure interactively

### "Module not found"

- Ensure you've run `pip install -r requirements.txt`
- Check you're in the project directory

### GitHub authentication fails

- Verify your token has `repo` scope
- Check the token hasn't expired

## Notes

- All repositories are created as **private** by default
- The Antigravity/Claude Code integration is currently simulated (see `modules/antigravity_runner.py`)
- LinkedIn integration requires developer app approval
- All data stays local except API calls to AI services

## Next Steps

After generating your first project:

1. Review the generated code in the GitHub repo
2. Clone it locally: `git clone <repo-url>`
3. Follow the README in the generated project
4. Customize as needed
5. Use it in your portfolio!
