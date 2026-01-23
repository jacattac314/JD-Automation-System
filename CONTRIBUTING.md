# Contributing to JD Automation System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run tests:

   ```bash
   pytest tests/ -v
   ```

## Project Structure

```
jd-automation/
├── cli/              # Command-line interface
├── core/             # Core orchestration logic
├── modules/          # Service modules
├── tests/            # Test suite
├── examples/         # Example job descriptions
└── docs/             # Additional documentation
```

## Making Changes

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make your changes**: Follow coding standards below
3. **Add tests**: Ensure new features have test coverage
4. **Run tests**: `pytest tests/ -v`
5. **Commit**: Use clear, descriptive commit messages
6. **Push**: `git push origin feature/your-feature-name`
7. **Pull Request**: Open a PR with description of changes

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for all functions/classes

### Documentation

- Update README.md if adding new features
- Add docstrings to new modules/functions
- Update ARCHITECTURE.md for architectural changes

### Testing

- Write unit tests for new modules
- Maintain test coverage above 70%
- Use pytest fixtures for common setups
- Mock external API calls

## Module Development

### Adding a New Module

1. Create file in `modules/` directory
2. Follow this template:

```python
"""
Module description.

Brief description of what this module does.
"""

from loguru import logger
from typing import Dict, Any

class YourService:
    """Service description."""
    
    def __init__(self):
        """Initialize service."""
        pass
    
    def your_method(self, input: str) -> Dict[str, Any]:
        """
        Method description.
        
        Args:
            input: Description
            
        Returns:
            Description of return value
        """
        logger.info("Starting operation")
        # Implementation
        return {}
```

1. Add tests in `tests/test_your_module.py`
2. Import in orchestrator if needed
3. Update documentation

### Adding Project Templates

To add new project templates to the ideation system:

1. Edit `modules/ideation.py`
2. Add to `PROJECT_TEMPLATES` dict:

```python
"category_name": [
    {
        "title": "Project Name",
        "description": "Description",
        "skills": ["skill1", "skill2"]
    }
]
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_modules.py::test_jd_analyzer -v

# With coverage
pytest tests/ --cov=modules --cov-report=html
```

### Writing Tests

```python
def test_your_feature():
    """Test description."""
    # Setup
    service = YourService()
    
    # Execute
    result = service.method(input)
    
    # Assert
    assert result["key"] == expected_value
```

## Areas for Contribution

### High Priority

- [ ] Real Antigravity/Claude Code integration
- [ ] Web UI implementation
- [ ] Improved NLP for JD analysis
- [ ] More project templates
- [ ] Enhanced error recovery

### Medium Priority

- [ ] Batch processing multiple JDs
- [ ] Template customization UI
- [ ] Analytics and metrics
- [ ] Export/import configurations
- [ ] GitLab/Bitbucket support

### Nice to Have

- [ ] Mobile app for monitoring
- [ ] Slack/Discord notifications
- [ ] Project showcase gallery
- [ ] Template marketplace

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design changes
- Add examples in `examples/` directory
- Document breaking changes in PR description

## Questions?

- Open an issue for bugs or feature requests
- Tag maintainers in complex PRs
- Join discussions in issues

## Code Review Process

1. Automated tests must pass
2. Code review by at least one maintainer
3. Documentation must be updated
4. No merge conflicts

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🚀
