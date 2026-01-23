"""
Gemini Client Module.

Generates technical specifications using Google's Gemini Deep Research.
"""

import google.generativeai as genai
from loguru import logger
from typing import Dict, List, Any

from core.config import config


class GeminiClient:
    """Client for Google Gemini API."""
    
    def __init__(self):
        if not config.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_specification(
        self,
        job_description: str,
        project_idea: Dict[str, Any],
        skills: List[str]
    ) -> str:
        """
        Generate a comprehensive application specification.

        Args:
            job_description: The original JD
            project_idea: Selected project idea
            skills: Extracted skills

        Returns:
            Markdown-formatted specification document

        Raises:
            ValueError: If required inputs are missing or invalid
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty")
        if not project_idea or not project_idea.get('title'):
            raise ValueError("Project idea must have a title")
        if not skills:
            raise ValueError("Skills list cannot be empty")

        logger.info(f"Generating specification for: {project_idea['title']}")
        
        prompt = self._build_specification_prompt(job_description, project_idea, skills)
        
        try:
            response = self.model.generate_content(prompt)
            spec = response.text
            
            logger.info(f"Generated specification: {len(spec)} characters")
            return spec
            
        except Exception as e:
            logger.error(f"Failed to generate specification: {e}")
            # Return a fallback spec
            return self._generate_fallback_spec(project_idea, skills)
    
    def _build_specification_prompt(
        self,
        jd: str,
        project_idea: Dict[str, Any],
        skills: List[str]
    ) -> str:
        """Build the prompt for specification generation."""
        return f"""You are a senior technical architect tasked with creating a comprehensive application specification.

**Context:**
A candidate is applying for a role described in this job description:
---
{jd[:1000]}
---

**Project Concept:**
Title: {project_idea['title']}
Description: {project_idea['description']}

**Required Skills to Demonstrate:**
{', '.join(skills[:10])}

**Task:**
Create a detailed, production-ready Application Specification Document that includes:

1. **Executive Summary**
   - Project overview and objectives
   - Key value propositions

2. **System Architecture**
   - High-level architecture diagram (describe in text)
   - Component breakdown
   - Data flow

3. **Technical Stack**
   - Frontend technologies
   - Backend technologies
   - Database and storage
   - Infrastructure and deployment

4. **Core Features**
   - List 5-8 key features with detailed descriptions
   - User stories for each feature

5. **Implementation Plan**
   - Phase 1: Foundation (setup, basic structure)
   - Phase 2: Core Features (main functionality)
   - Phase 3: Polish & Deployment (testing, deployment)
   - Estimated timeline for each phase

6. **API Design**
   - Key endpoints (if applicable)
   - Data models/schemas

7. **Security Considerations**
   - Authentication/authorization
   - Data protection
   - Best practices

8. **Testing Strategy**
   - Unit testing approach
   - Integration testing
   - End-to-end testing

9. **Deployment Plan**
   - Environment setup
   - CI/CD pipeline
   - Monitoring and logging

Format the output as a well-structured Markdown document with proper headings, bullet points, and code blocks where appropriate.
Be specific and technical - this will be used by an AI coding agent to implement the project.
"""
    
    def _generate_fallback_spec(self, project_idea: Dict[str, Any], skills: List[str]) -> str:
        """Generate a basic fallback specification if API fails."""
        return f"""# {project_idea['title']} - Technical Specification

## Overview
{project_idea['description']}

## Objectives
- Demonstrate proficiency in {', '.join(skills[:5])}
- Build a production-ready application
- Showcase best practices in software development

## Technical Stack
**Skills Used:** {', '.join(skills)}

## Core Features
1. User authentication and authorization
2. RESTful API design
3. Database integration
4. Responsive UI/UX
5. Automated testing

## Implementation Plan

### Phase 1: Foundation
- Project setup and structure
- Database schema design
- Basic API endpoints

### Phase 2: Core Development
- Implement main features
- Frontend components
- Integration testing

### Phase 3: Polish & Deploy
- UI/UX refinement
- Performance optimization
- Deployment configuration

## Architecture
This application follows modern best practices with:
- Clean separation of concerns
- RESTful API design
- Responsive frontend
- Secure authentication
- Comprehensive testing

## Next Steps
1. Set up development environment
2. Initialize project structure
3. Implement features incrementally
4. Test throughout development
5. Deploy to production

---
*Generated automatically by JD Automation System*
"""
