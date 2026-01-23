"""
Demo script to test the system without requiring full API configuration.
This creates a mock run to demonstrate the pipeline.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.jd_analysis import JDAnalyzer
from modules.ideation import ProjectIdeation

def demo_analysis_and_ideation():
    """Demo the analysis and ideation modules."""
    
    print("=" * 60)
    print("JD AUTOMATION SYSTEM - DEMO MODE")
    print("=" * 60)
    print()
    
    # Sample job description
    jd = """
    Senior Full-Stack Software Engineer
    
    We're seeking an experienced engineer with:
    - 5+ years in Python and JavaScript
    - React and Node.js expertise
    - PostgreSQL database experience
    - AWS cloud knowledge
    - REST API development
    - Docker and CI/CD experience
    
    Responsibilities include building scalable web applications,
    mentoring junior developers, and architecting solutions.
    """
    
    print("📄 JOB DESCRIPTION:")
    print("-" * 60)
    print(jd.strip())
    print()
    
    # Step 1: Analyze JD
    print("🔍 STEP 1: Analyzing Job Description...")
    analyzer = JDAnalyzer()
    skills = analyzer.extract_skills(jd)
    
    print(f"   ✓ Extracted {len(skills)} skills:")
    for skill in skills[:10]:
        print(f"     • {skill}")
    if len(skills) > 10:
        print(f"     ... and {len(skills) - 10} more")
    print()
    
    # Step 2: Generate project idea
    print("💡 STEP 2: Generating Project Idea...")
    ideation = ProjectIdeation()
    project = ideation.generate_idea(jd, skills)
    
    print(f"   ✓ Project Title: {project['title']}")
    print(f"   ✓ Description: {project['description']}")
    print(f"   ✓ Category: {project.get('role', 'Software Engineering')}")
    print(f"   ✓ Key Technologies: {', '.join(project['skills_used'][:5])}")
    print()
    
    # Show what would happen next
    print("📦 NEXT STEPS (in full mode):")
    print("   3. Create GitHub repository")
    print("   4. Generate specification with Gemini AI")
    print("   5. Implement project with Claude Code")
    print("   6. Organize artifacts and documentation")
    print("   7. Push to GitHub")
    print("   8. Add to LinkedIn profile")
    print()
    
    print("=" * 60)
    print("✅ DEMO COMPLETE!")
    print("=" * 60)
    print()
    print("To run the full pipeline:")
    print("  1. Configure API keys: python -m cli.main setup")
    print("  2. Run: python -m cli.main run --jd-file examples/sample_jd.txt")
    print()

if __name__ == "__main__":
    demo_analysis_and_ideation()
