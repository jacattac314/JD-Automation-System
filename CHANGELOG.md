# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-23

### Added

- Initial implementation of JD Automation System
- Core orchestration engine with sequential pipeline execution
- JD analysis module with skill extraction
- Project ideation module with template matching
- GitHub integration for repository creation and publishing
- Gemini client for specification generation
- Antigravity runner interface (simulated for now)
- Artifact manager for project organization
- LinkedIn integration for profile projects
- CLI interface with Rich formatting
- Configuration management with secure credential storage
- Comprehensive logging and audit trail
- Unit tests for core modules
- Example job description
- Documentation:
  - README.md with project overview
  - QUICKSTART.md with usage guide
  - ARCHITECTURE.md with design documentation
  - CONTRIBUTING.md with development guidelines
  - This CHANGELOG.md

### Security

- API keys stored in OS keyring with .env fallback
- Private GitHub repositories by default
- No credentials logged or committed

### Notes

- Antigravity/Claude Code integration is currently simulated
- LinkedIn API requires developer app approval
- All operations are local-first with minimal cloud dependencies

## [Unreleased]

### Planned

- Real Antigravity/Claude Code integration
- Web UI dashboard
- Batch processing for multiple JDs
- Enhanced NLP for JD analysis
- More project templates
- Resume capability for failed runs
- GitLab and Bitbucket support
- Analytics and metrics
- Template marketplace
