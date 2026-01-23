"""
Basic tests for JD Automation System.
"""

import pytest
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.jd_analysis import JDAnalyzer
from modules.ideation import ProjectIdeation


def test_jd_analyzer():
    """Test JD analysis."""
    analyzer = JDAnalyzer()
    
    jd = """
    We're looking for a Senior Full-Stack Developer with expertise in:
    - Python and Django
    - React and JavaScript
    - PostgreSQL databases
    - AWS cloud services
    - REST API development
    
    5+ years of experience required.
    """
    
    skills = analyzer.extract_skills(jd)
    
    assert "Python" in skills
    assert "React" in skills
    assert "PostgreSQL" in skills
    assert "AWS" in skills
    assert len(skills) > 0


def test_project_ideation():
    """Test project ideation."""
    ideation = ProjectIdeation()
    
    jd = "Full-stack developer with Python, React, and PostgreSQL"
    skills = ["Python", "React", "PostgreSQL", "REST"]
    
    project = ideation.generate_idea(jd, skills)
    
    assert "title" in project
    assert "description" in project
    assert len(project["title"]) > 0


def test_skill_categorization():
    """Test skill categorization."""
    ideation = ProjectIdeation()

    # ML skills
    ml_skills = ["Python", "Machine Learning", "Deep Learning", "NLP"]
    category = ideation._categorize_skills(ml_skills)
    assert category == "data_ml"

    # Web skills
    web_skills = ["React", "Node.js", "JavaScript", "REST"]
    category = ideation._categorize_skills(web_skills)
    assert category == "web_fullstack"


def test_jd_analyzer_empty_input():
    """Test JD analyzer rejects empty input."""
    analyzer = JDAnalyzer()

    with pytest.raises(ValueError, match="cannot be empty"):
        analyzer.extract_skills("")

    with pytest.raises(ValueError, match="cannot be empty"):
        analyzer.extract_skills("   ")

    with pytest.raises(ValueError, match="cannot be empty"):
        analyzer.extract_skills(None)


def test_ideation_empty_input():
    """Test ideation rejects empty input."""
    ideation = ProjectIdeation()

    with pytest.raises(ValueError, match="Job description cannot be empty"):
        ideation.generate_idea("", ["Python"])

    with pytest.raises(ValueError, match="Skills list cannot be empty"):
        ideation.generate_idea("Some job description", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
