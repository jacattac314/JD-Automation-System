"""
Job Description Analysis Module (DEPRECATED).

This module was part of the original JD-based flow. The new flow uses
Gemini AI for idea enhancement and PRD generation instead.

Kept for backward compatibility. Use modules/gemini_client.py enhance_idea() instead.
"""

import re
from typing import List, Dict, Any
from loguru import logger


class JDAnalyzer:
    """Analyzes job descriptions to extract key information."""
    
    # Common tech skills to look for
    TECH_KEYWORDS = [
        "python", "javascript", "java", "c++", "c#", "go", "rust", "ruby", "php",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "sql", "postgresql", "mysql", "mongodb", "redis",
        "git", "ci/cd", "jenkins", "github actions",
        "machine learning", "deep learning", "ai", "nlp", "computer vision",
        "rest", "graphql", "microservices", "api",
        "agile", "scrum", "tdd", "unit testing"
    ]
    
    def extract_skills(self, job_description: str) -> List[str]:
        """
        Extract technical skills from job description.

        Args:
            job_description: The JD text

        Returns:
            List of identified skills

        Raises:
            ValueError: If job_description is empty or None
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty or None")

        jd_lower = job_description.lower()
        skills = []
        
        # Find tech keywords
        for keyword in self.TECH_KEYWORDS:
            if keyword in jd_lower:
                # Add proper casing
                skills.append(self._proper_case(keyword))
        
        # Remove duplicates and sort
        skills = sorted(list(set(skills)))
        
        logger.info(f"Extracted {len(skills)} skills from JD")
        
        return skills
    
    def _proper_case(self, keyword: str) -> str:
        """Convert keyword to proper case."""
        casing_map = {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "node.js": "Node.js",
            "react": "React",
            "angular": "Angular",
            "vue": "Vue.js",
            "c++": "C++",
            "c#": "C#",
            "aws": "AWS",
            "gcp": "GCP",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "graphql": "GraphQL",
            "github actions": "GitHub Actions",
            "ci/cd": "CI/CD",
            "rest": "REST",
            "api": "API",
            "nlp": "NLP",
            "ai": "AI",
            "ml": "ML",
            "tdd": "TDD"
        }
        
        return casing_map.get(keyword.lower(), keyword.title())
    
    def extract_requirements(self, job_description: str) -> Dict[str, Any]:
        """
        Extract structured requirements from JD.

        Args:
            job_description: The JD text

        Returns:
            Dictionary with categorized requirements

        Raises:
            ValueError: If job_description is empty or None
        """
        # extract_skills already validates input
        skills = self.extract_skills(job_description)
        
        # Look for experience level
        experience = self._extract_experience_level(job_description)
        
        # Look for key responsibilities
        responsibilities = self._extract_responsibilities(job_description)
        
        return {
            "skills": skills,
            "experience_level": experience,
            "responsibilities": responsibilities
        }
    
    def _extract_experience_level(self, jd: str) -> str:
        """Extract experience level from JD."""
        jd_lower = jd.lower()
        
        if any(term in jd_lower for term in ["senior", "lead", "principal", "staff"]):
            return "senior"
        elif any(term in jd_lower for term in ["mid-level", "intermediate", "3-5 years", "3+ years"]):
            return "mid"
        elif any(term in jd_lower for term in ["junior", "entry", "0-2 years", "new grad"]):
            return "junior"
        
        return "mid"  # Default
    
    def _extract_responsibilities(self, jd: str) -> List[str]:
        """Extract key responsibilities."""
        # Look for common responsibility patterns
        responsibilities = []
        
        patterns = [
            r"(?:you will|you'll|responsibilities include)[\s:]+(.+?)(?:\n\n|\.\s+[A-Z]|$)",
            r"(?:responsibilities|duties)[\s:]+(.+?)(?:\n\n|qualifications|requirements|$)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, jd, re.IGNORECASE | re.DOTALL)
            if matches:
                # Split by bullet points or newlines
                text = matches[0]
                items = re.split(r'[•\-\*]\s+|\n', text)
                responsibilities.extend([item.strip() for item in items if item.strip() and len(item.strip()) > 10])
        
        return responsibilities[:5]  # Return top 5
