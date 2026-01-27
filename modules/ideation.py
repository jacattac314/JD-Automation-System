"""
Project Ideation Module (DEPRECATED).

This module was part of the original JD-based flow that used hardcoded templates.
The new flow uses the user's own application idea enhanced by Gemini AI.

Kept for backward compatibility. Use modules/gemini_client.py enhance_idea() instead.
"""

import random
from typing import Dict, List, Any
from loguru import logger


class ProjectIdeation:
    """Generates relevant project ideas based on job requirements."""
    
    # Project templates categorized by skills
    PROJECT_TEMPLATES = {
        "web_fullstack": [
            {
                "title": "Real-time Collaboration Platform",
                "description": "A full-stack web application with real-time features, user authentication, and responsive UI",
                "skills": ["react", "node.js", "websockets", "postgresql"]
            },
            {
                "title": "E-Commerce Product Management System",
                "description": "Complete e-commerce backend with inventory management, order processing, and payment integration",
                "skills": ["python", "django", "rest", "postgresql"]
            },
            {
                "title": "Task Management Dashboard",
                "description": "Feature-rich project management tool with drag-and-drop, filtering, and team collaboration",
                "skills": ["react", "typescript", "rest api", "mongodb"]
            }
        ],
        "data_ml": [
            {
                "title": "Predictive Analytics Dashboard",
                "description": "ML-powered analytics platform with visualization, training pipeline, and model deployment",
                "skills": ["python", "machine learning", "fastapi", "postgresql"]
            },
            {
                "title": "NLP Sentiment Analysis API",
                "description": "Natural language processing service for sentiment analysis with REST API and fine-tuned models",
                "skills": ["python", "nlp", "deep learning", "docker"]
            }
        ],
        "cloud_devops": [
            {
                "title": "Multi-Cloud Infrastructure Manager",
                "description": "Infrastructure-as-code solution for managing resources across AWS, Azure, and GCP",
                "skills": ["terraform", "aws", "kubernetes", "ci/cd"]
            },
            {
                "title": "Automated CI/CD Pipeline",
                "description": "Complete DevOps pipeline with automated testing, deployment, and monitoring",
                "skills": ["docker", "kubernetes", "github actions", "monitoring"]
            }
        ],
        "mobile": [
            {
                "title": "Cross-Platform Mobile App",
                "description": "Feature-complete mobile application with offline support and cloud sync",
                "skills": ["react native", "typescript", "rest api", "firebase"]
            }
        ]
    }
    
    def generate_idea(self, job_description: str, skills: List[str]) -> Dict[str, Any]:
        """
        Generate a project idea based on JD and skills.

        Args:
            job_description: The JD text
            skills: Extracted skills list

        Returns:
            Project idea dictionary with title, description, and rationale

        Raises:
            ValueError: If job_description or skills are empty/None
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty or None")
        if not skills:
            raise ValueError("Skills list cannot be empty")

        logger.info(f"Generating project idea for skills: {skills[:5]}")
        
        # Determine category based on skills
        category = self._categorize_skills(skills)
        
        # Get templates for category
        templates = self.PROJECT_TEMPLATES.get(category, self.PROJECT_TEMPLATES["web_fullstack"])
        
        # Score and select best template
        scored_templates = []
        for template in templates:
            score = self._score_template(template, skills)
            scored_templates.append((score, template))
        
        # Sort by score and pick best
        scored_templates.sort(reverse=True, key=lambda x: x[0])
        best_template = scored_templates[0][1]
        
        # Customize the template
        project = self._customize_template(best_template, skills, job_description)
        
        logger.info(f"Selected project: {project['title']}")
        return project
    
    def _categorize_skills(self, skills: List[str]) -> str:
        """Determine primary category from skills."""
        skills_lower = [s.lower() for s in skills]
        
        # Count matches for each category
        ml_count = sum(1 for s in skills_lower if s in ["python", "machine learning", "deep learning", "ai", "nlp", "tensorflow", "pytorch"])
        web_count = sum(1 for s in skills_lower if s in ["react", "angular", "vue", "node.js", "django", "flask", "javascript"])
        cloud_count = sum(1 for s in skills_lower if s in ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"])
        mobile_count = sum(1 for s in skills_lower if s in ["react native", "flutter", "swift", "kotlin"])
        
        if ml_count >= 2:
            return "data_ml"
        elif cloud_count >= 2:
            return "cloud_devops"
        elif mobile_count >= 1:
            return "mobile"
        else:
            return "web_fullstack"
    
    def _score_template(self, template: Dict[str, Any], skills: List[str]) -> float:
        """Score how well a template matches the skills."""
        skills_lower = [s.lower() for s in skills]
        template_skills_lower = [s.lower() for s in template["skills"]]
        
        # Count matching skills
        matches = sum(1 for ts in template_skills_lower if any(ts in skill or skill in ts for skill in skills_lower))
        
        # Score is percentage of template skills that match
        return matches / len(template_skills_lower) if template_skills_lower else 0
    
    def _customize_template(self, template: Dict[str, Any], skills: List[str], jd: str) -> Dict[str, Any]:
        """Customize the template with specific skills."""
        # Extract role from JD if possible
        role = "Software Engineering"
        if "data scientist" in jd.lower():
            role = "Data Science"
        elif "devops" in jd.lower() or "sre" in jd.lower():
            role = "DevOps/SRE"
        elif "full stack" in jd.lower() or "full-stack" in jd.lower():
            role = "Full-Stack Development"
        elif "backend" in jd.lower():
            role = "Backend Development"
        elif "frontend" in jd.lower() or "front-end" in jd.lower():
            role = "Frontend Development"
        
        return {
            "title": template["title"],
            "description": template["description"],
            "skills_used": skills[:8],  # Top skills
            "template_skills": template["skills"],
            "role": role
        }
