# Deployment Guide

## Local Deployment (Recommended)

This system is designed to run locally on your development machine.

### Prerequisites

- Windows 10/11, macOS 10.15+, or Linux
- Python 3.10 or higher
- Git 2.30+
- Internet connection for API calls

### Installation Steps

1. **Clone the repository:**

```bash
git clone <repo-url>
cd "Application Generator"
```

1. **Create virtual environment:**

```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

1. **Configure environment:**

```bash
# Copy example
cp .env.example .env

# Run setup wizard
python -m cli.main setup
```

### API Key Setup

#### Gemini API (Required)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Add to configuration: `GEMINI_API_KEY=your_key_here`

#### GitHub (Required)

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Create new Personal Access Token (classic)
3. Select scopes: `repo` (full control of private repositories)
4. Add to configuration: `GITHUB_TOKEN=ghp_your_token_here`
5. Set username: `GITHUB_USERNAME=your_username`

#### Anthropic (Required for Claude Code)

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create API key
3. Add to configuration: `ANTHROPIC_API_KEY=sk-ant-your_key_here`

#### LinkedIn (Optional)

1. Create app at [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Request "Profile Edit" permissions (requires approval)
3. Generate OAuth 2.0 token
4. Add to configuration: `LINKEDIN_ACCESS_TOKEN=your_token_here`
5. Enable: `ENABLE_LINKEDIN_INTEGRATION=true`

### Verification

Test the installation:

```bash
# Run demo (no API keys needed)
python demo.py

# Run tests
pytest tests/ -v

# Check CLI
python -m cli.main --help
```

## Running the System

### Basic Usage

```bash
# Single run with file
python -m cli.main run --jd-file examples/sample_jd.txt

# Single run with inline text
python -m cli.main run --jd "Your job description..."

# Skip LinkedIn
python -m cli.main run --jd-file examples/sample_jd.txt --no-linkedin
```

### View History

```bash
python -m cli.main history
```

## Docker Deployment (Optional)

For isolated execution, you can run in Docker:

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data logs projects

ENTRYPOINT ["python", "-m", "cli.main"]
CMD ["--help"]
```

### Build and Run

```bash
# Build
docker build -t jd-automation .

# Run with mounted config
docker run -v $(pwd)/.env:/app/.env -v $(pwd)/projects:/app/projects jd-automation run --jd-file examples/sample_jd.txt
```

## Cloud Deployment (Advanced)

While designed for local use, you can deploy to a cloud VM for scheduled runs:

### AWS EC2 Example

1. Launch EC2 instance (t3.small or larger)
2. SSH into instance
3. Follow local installation steps
4. Set up cron for scheduled runs:

```bash
# Edit crontab
crontab -e

# Add daily run at 2 AM
0 2 * * * cd /home/ubuntu/jd-automation && /home/ubuntu/jd-automation/venv/bin/python -m cli.main run --jd-file daily_jd.txt
```

### Security Considerations for Cloud

- Use instance IAM roles instead of hardcoded credentials
- Store secrets in AWS Secrets Manager or similar
- Use VPC and security groups to restrict access
- Enable CloudWatch logging
- Use spot instances to reduce costs

## Monitoring

### Logs

- Application logs: `logs/jd_automation_*.log`
- Run history: `data/runs.json`
- Individual run logs: `projects/<project>/logs/`

### Health Checks

```bash
# Verify configuration
python -c "from core.config import config; valid, errors = config.validate(); print('Valid' if valid else errors)"

# Check API access
python -c "from modules.github_service import GitHubService; g = GitHubService(); print(g.user.login)"
```

## Troubleshooting

### Common Issues

**"Configuration errors"**

- Ensure all required API keys are set
- Run `python -m cli.main setup` to reconfigure

**"Module not found"**

- Activate virtual environment
- Reinstall: `pip install -r requirements.txt`

**GitHub push fails**

- Check token has `repo` scope
- Verify token hasn't expired
- Ensure username is correct

**Gemini API errors**

- Check API key is valid
- Verify billing is enabled
- Check rate limits

### Debug Mode

```bash
# Set log level to DEBUG in .env
LOG_LEVEL=DEBUG

# View detailed logs
tail -f logs/jd_automation_*.log
```

## Backup and Recovery

### Backup Important Data

```bash
# Backup configuration
cp .env .env.backup

# Backup run history
cp data/runs.json data/runs.json.backup

# Projects are already on GitHub (if runs completed)
```

### Recovery

- Configuration: Restore from `.env.backup`
- History: Restore from `data/runs.json.backup`
- Projects: Clone from GitHub

## Updates

### Updating the System

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Check changelog
cat CHANGELOG.md
```

## Performance Optimization

### Reduce API Costs

- Cache Gemini specifications for similar JDs
- Use lower-cost models where appropriate
- Batch multiple runs when possible

### Speed Up Execution

- Pre-warm AI models (if running locally)
- Use SSD for projects directory
- Increase timeout limits for complex projects

## Scaling

For processing many JDs:

1. Set up multiple instances
2. Use a queue system (e.g., RabbitMQ)
3. Distribute JDs across instances
4. Aggregate results in central database

---

For additional help, see [QUICKSTART.md](QUICKSTART.md) or open an issue.
