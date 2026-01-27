"""
Gemini Client Module.

Generates enhanced app descriptions and comprehensive PRDs using Google's Gemini AI.
"""

import json
import google.generativeai as genai
from loguru import logger
from typing import Dict, List, Any, Optional


from core.config import config


class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(self):
        if not config.gemini_api_key:
            raise ValueError("Gemini API key not configured")

        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def enhance_idea(self, app_idea: str, tech_preferences: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance a raw application idea into a structured product concept.

        Args:
            app_idea: The user's raw application idea
            tech_preferences: Optional technology preferences from the user

        Returns:
            Structured dict with title, description, target_users, problem_statement,
            key_value_props, and suggested_tech_stack

        Raises:
            ValueError: If app_idea is empty or None
        """
        if not app_idea or not app_idea.strip():
            raise ValueError("Application idea cannot be empty")

        logger.info("Enhancing application idea with Gemini AI")

        prompt = self._build_enhance_prompt(app_idea, tech_preferences)

        try:
            response = self.model.generate_content(prompt)
            text = response.text

            # Try to parse JSON from the response
            enhanced = self._parse_json_response(text)
            if enhanced and "title" in enhanced:
                logger.info(f"Enhanced idea: {enhanced['title']}")
                return enhanced

            # If JSON parsing fails, return a structured fallback from the text
            return self._generate_fallback_enhanced_idea(app_idea, tech_preferences)

        except Exception as e:
            logger.error(f"Failed to enhance idea: {e}")
            return self._generate_fallback_enhanced_idea(app_idea, tech_preferences)

    def generate_prd(self, enhanced_idea: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive PRD with epics, user stories, and features.

        Args:
            enhanced_idea: The AI-enhanced idea dict from enhance_idea()

        Returns:
            Dict with 'prd' (structured data) and 'prd_markdown' (formatted document)

        Raises:
            ValueError: If enhanced_idea is missing required fields
        """
        if not enhanced_idea or not enhanced_idea.get("title"):
            raise ValueError("Enhanced idea must have a title")

        logger.info(f"Generating PRD for: {enhanced_idea['title']}")

        prompt = self._build_prd_prompt(enhanced_idea)

        try:
            response = self.model.generate_content(prompt)
            text = response.text

            # Try to parse structured JSON from the response
            prd_data = self._parse_json_response(text)
            if prd_data and "epics" in prd_data:
                prd_markdown = self._prd_to_markdown(prd_data, enhanced_idea)
                logger.info(f"Generated PRD with {len(prd_data.get('epics', []))} epics")
                return {"prd": prd_data, "prd_markdown": prd_markdown}

            # If JSON parsing fails, treat the text as markdown and build structure
            prd_data = self._generate_fallback_prd(enhanced_idea)
            return {
                "prd": prd_data,
                "prd_markdown": text if len(text) > 200 else self._prd_to_markdown(prd_data, enhanced_idea)
            }

        except Exception as e:
            logger.error(f"Failed to generate PRD: {e}")
            prd_data = self._generate_fallback_prd(enhanced_idea)
            return {
                "prd": prd_data,
                "prd_markdown": self._prd_to_markdown(prd_data, enhanced_idea)
            }

    # ---- Prompt builders ----

    def _build_enhance_prompt(self, app_idea: str, tech_preferences: Optional[str] = None) -> str:
        """Build prompt for idea enhancement."""
        tech_section = ""
        if tech_preferences:
            tech_section = f"""
The user has the following technology preferences:
{tech_preferences}
Incorporate these into the suggested tech stack where appropriate.
"""

        return f"""You are a senior product strategist. A user has provided a rough application idea.
Your job is to enhance it into a clear, structured product concept.

**User's raw idea:**
{app_idea}
{tech_section}

**Return ONLY valid JSON** with this exact structure (no markdown, no extra text):
{{
  "title": "A concise, professional project name",
  "description": "2-3 paragraph detailed description of the application — what it does, how it works, and why it matters",
  "target_users": "Description of the primary user personas",
  "problem_statement": "The specific problem this application solves",
  "key_value_props": ["Value proposition 1", "Value proposition 2", "Value proposition 3"],
  "suggested_tech_stack": {{
    "frontend": ["technology1", "technology2"],
    "backend": ["technology1", "technology2"],
    "database": ["technology1"],
    "infrastructure": ["technology1", "technology2"]
  }}
}}

Be specific and practical. The output will be used to generate a full PRD next."""

    def _build_prd_prompt(self, enhanced_idea: Dict[str, Any]) -> str:
        """Build prompt for PRD generation."""
        return f"""You are a senior product manager creating a comprehensive Product Requirements Document (PRD).

**Application Concept:**
Title: {enhanced_idea.get('title', 'Untitled')}
Description: {enhanced_idea.get('description', '')}
Target Users: {enhanced_idea.get('target_users', 'General users')}
Problem Statement: {enhanced_idea.get('problem_statement', '')}
Key Value Props: {json.dumps(enhanced_idea.get('key_value_props', []))}
Suggested Tech Stack: {json.dumps(enhanced_idea.get('suggested_tech_stack', {{}}))}

**Return ONLY valid JSON** with this exact structure (no markdown, no extra text):
{{
  "product_overview": {{
    "vision": "Product vision statement",
    "goals": ["Goal 1", "Goal 2", "Goal 3"],
    "success_metrics": ["Metric 1", "Metric 2"]
  }},
  "epics": [
    {{
      "name": "Epic Name",
      "description": "What this epic covers",
      "priority": "P0",
      "user_stories": [
        {{
          "title": "User Story Title",
          "story": "As a [user], I want [feature] so that [benefit]",
          "acceptance_criteria": [
            "Given [context], when [action], then [outcome]"
          ],
          "features": [
            {{
              "name": "Feature name",
              "description": "What to implement",
              "complexity": "S"
            }}
          ]
        }}
      ]
    }}
  ],
  "technical_architecture": {{
    "overview": "High-level architecture description",
    "components": ["Component 1", "Component 2"],
    "data_model": [
      {{
        "entity": "EntityName",
        "fields": ["field1: type", "field2: type"],
        "relationships": "Description of relationships"
      }}
    ],
    "api_endpoints": [
      {{
        "method": "GET",
        "path": "/api/resource",
        "description": "What it does"
      }}
    ]
  }},
  "non_functional_requirements": {{
    "performance": ["Requirement 1"],
    "security": ["Requirement 1"],
    "scalability": ["Requirement 1"]
  }},
  "implementation_roadmap": {{
    "mvp_scope": "Description of MVP",
    "phases": [
      {{
        "name": "Phase 1: Foundation",
        "epics": ["Epic Name"],
        "description": "What this phase covers"
      }}
    ]
  }}
}}

Create 4-6 epics with 3-5 user stories each. Each user story should have 2-4 acceptance criteria and 1-3 features.
Be specific and technical — this will be used by an AI coding agent to implement the project."""

    # ---- Response parsing ----

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to extract and parse JSON from a Gemini response."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown code fences
        import re
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        brace_start = text.find('{')
        brace_end = text.rfind('}')
        if brace_start != -1 and brace_end != -1:
            try:
                return json.loads(text[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass

        return None

    # ---- Fallback generators ----

    def _generate_fallback_enhanced_idea(self, app_idea: str, tech_preferences: Optional[str] = None) -> Dict[str, Any]:
        """Generate a basic enhanced idea if API fails."""
        # Derive a title from the first sentence
        title = app_idea.strip().split('.')[0].split('\n')[0][:80]
        if len(title) < 5:
            title = "Application Project"

        tech_stack = {"frontend": ["React", "TypeScript"], "backend": ["Python", "FastAPI"],
                      "database": ["PostgreSQL"], "infrastructure": ["Docker"]}
        if tech_preferences:
            tech_stack["notes"] = tech_preferences

        return {
            "title": title,
            "description": app_idea,
            "target_users": "End users who need the described functionality",
            "problem_statement": f"Users need: {app_idea[:200]}",
            "key_value_props": [
                "Solves the core user need",
                "Modern, maintainable architecture",
                "Production-ready implementation"
            ],
            "suggested_tech_stack": tech_stack
        }

    def _generate_fallback_prd(self, enhanced_idea: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic PRD structure if API fails."""
        title = enhanced_idea.get("title", "Application")
        description = enhanced_idea.get("description", "")

        return {
            "product_overview": {
                "vision": f"Build {title} — {description[:100]}",
                "goals": [
                    "Deliver core functionality as described",
                    "Provide clean, maintainable codebase",
                    "Include comprehensive documentation"
                ],
                "success_metrics": [
                    "All core features implemented and functional",
                    "Application runs without errors"
                ]
            },
            "epics": [
                {
                    "name": "Project Foundation",
                    "description": "Set up project structure, configuration, and development environment",
                    "priority": "P0",
                    "user_stories": [
                        {
                            "title": "Project Initialization",
                            "story": "As a developer, I want a well-structured project so that I can develop efficiently",
                            "acceptance_criteria": [
                                "Project structure follows best practices",
                                "Dependencies are defined and installable",
                                "Configuration is externalized"
                            ],
                            "features": [
                                {"name": "Project scaffolding", "description": "Create directory structure and config files", "complexity": "S"},
                                {"name": "Dependency management", "description": "Set up package management and lock files", "complexity": "S"}
                            ]
                        }
                    ]
                },
                {
                    "name": "Core Features",
                    "description": "Implement the primary application functionality",
                    "priority": "P0",
                    "user_stories": [
                        {
                            "title": "Main Application Logic",
                            "story": "As a user, I want the core features so that I can accomplish my goals",
                            "acceptance_criteria": [
                                "Core functionality works as described",
                                "Error handling is in place",
                                "User feedback is clear"
                            ],
                            "features": [
                                {"name": "Core business logic", "description": "Implement main application features", "complexity": "L"},
                                {"name": "User interface", "description": "Build the primary user-facing interface", "complexity": "M"}
                            ]
                        }
                    ]
                },
                {
                    "name": "Data Layer",
                    "description": "Set up data storage, models, and access patterns",
                    "priority": "P0",
                    "user_stories": [
                        {
                            "title": "Data Persistence",
                            "story": "As a user, I want my data to persist so that I can access it later",
                            "acceptance_criteria": [
                                "Data is stored reliably",
                                "CRUD operations work correctly",
                                "Data validation is enforced"
                            ],
                            "features": [
                                {"name": "Database schema", "description": "Define data models and relationships", "complexity": "M"},
                                {"name": "Data access layer", "description": "Implement repository/DAO pattern", "complexity": "M"}
                            ]
                        }
                    ]
                },
                {
                    "name": "Testing & Quality",
                    "description": "Ensure application quality through automated testing",
                    "priority": "P1",
                    "user_stories": [
                        {
                            "title": "Automated Tests",
                            "story": "As a developer, I want automated tests so that I can refactor with confidence",
                            "acceptance_criteria": [
                                "Unit tests cover core logic",
                                "Integration tests verify workflows",
                                "Tests can be run with a single command"
                            ],
                            "features": [
                                {"name": "Unit tests", "description": "Write unit tests for core modules", "complexity": "M"},
                                {"name": "Integration tests", "description": "Write integration tests for key workflows", "complexity": "M"}
                            ]
                        }
                    ]
                }
            ],
            "technical_architecture": {
                "overview": f"Modern application architecture for {title}",
                "components": ["Frontend UI", "Backend API", "Database", "Configuration"],
                "data_model": [],
                "api_endpoints": []
            },
            "non_functional_requirements": {
                "performance": ["Application responds within 2 seconds for typical operations"],
                "security": ["Input validation on all user-facing endpoints", "Secrets managed via environment variables"],
                "scalability": ["Stateless design where possible"]
            },
            "implementation_roadmap": {
                "mvp_scope": "Project Foundation + Core Features + Data Layer",
                "phases": [
                    {"name": "Phase 1: Foundation", "epics": ["Project Foundation"], "description": "Set up structure and tooling"},
                    {"name": "Phase 2: Core", "epics": ["Core Features", "Data Layer"], "description": "Implement main functionality"},
                    {"name": "Phase 3: Quality", "epics": ["Testing & Quality"], "description": "Add tests and polish"}
                ]
            }
        }

    # ---- Markdown generation ----

    def _prd_to_markdown(self, prd: Dict[str, Any], enhanced_idea: Dict[str, Any]) -> str:
        """Convert structured PRD data to a formatted Markdown document."""
        lines = []
        title = enhanced_idea.get("title", "Application")

        lines.append(f"# Product Requirements Document: {title}")
        lines.append("")

        # Product overview
        overview = prd.get("product_overview", {})
        lines.append("## 1. Product Overview")
        lines.append("")
        lines.append(f"**Vision:** {overview.get('vision', '')}")
        lines.append("")
        if enhanced_idea.get("description"):
            lines.append(f"**Description:** {enhanced_idea['description']}")
            lines.append("")
        if enhanced_idea.get("target_users"):
            lines.append(f"**Target Users:** {enhanced_idea['target_users']}")
            lines.append("")
        if enhanced_idea.get("problem_statement"):
            lines.append(f"**Problem Statement:** {enhanced_idea['problem_statement']}")
            lines.append("")

        lines.append("### Goals")
        for goal in overview.get("goals", []):
            lines.append(f"- {goal}")
        lines.append("")

        lines.append("### Success Metrics")
        for metric in overview.get("success_metrics", []):
            lines.append(f"- {metric}")
        lines.append("")

        # Tech stack
        tech = enhanced_idea.get("suggested_tech_stack", {})
        if tech:
            lines.append("## 2. Technology Stack")
            lines.append("")
            for layer, techs in tech.items():
                if layer == "notes":
                    continue
                if isinstance(techs, list):
                    lines.append(f"- **{layer.title()}:** {', '.join(techs)}")
                else:
                    lines.append(f"- **{layer.title()}:** {techs}")
            lines.append("")

        # Epics and user stories
        lines.append("## 3. Epics & User Stories")
        lines.append("")
        for i, epic in enumerate(prd.get("epics", []), 1):
            lines.append(f"### Epic {i}: {epic['name']} [{epic.get('priority', 'P1')}]")
            lines.append(f"_{epic.get('description', '')}_")
            lines.append("")

            for j, story in enumerate(epic.get("user_stories", []), 1):
                lines.append(f"#### Story {i}.{j}: {story['title']}")
                lines.append(f"> {story.get('story', '')}")
                lines.append("")

                lines.append("**Acceptance Criteria:**")
                for ac in story.get("acceptance_criteria", []):
                    lines.append(f"- [ ] {ac}")
                lines.append("")

                lines.append("**Features:**")
                for feat in story.get("features", []):
                    complexity = feat.get("complexity", "M")
                    lines.append(f"- `[{complexity}]` **{feat['name']}** — {feat.get('description', '')}")
                lines.append("")

        # Technical architecture
        arch = prd.get("technical_architecture", {})
        if arch:
            lines.append("## 4. Technical Architecture")
            lines.append("")
            lines.append(arch.get("overview", ""))
            lines.append("")
            if arch.get("components"):
                lines.append("**Components:**")
                for comp in arch["components"]:
                    lines.append(f"- {comp}")
                lines.append("")
            if arch.get("data_model"):
                lines.append("### Data Model")
                for entity in arch["data_model"]:
                    lines.append(f"**{entity.get('entity', 'Entity')}**")
                    for field in entity.get("fields", []):
                        lines.append(f"  - {field}")
                    if entity.get("relationships"):
                        lines.append(f"  - _Relationships:_ {entity['relationships']}")
                    lines.append("")
            if arch.get("api_endpoints"):
                lines.append("### API Endpoints")
                for ep in arch["api_endpoints"]:
                    lines.append(f"- `{ep.get('method', 'GET')} {ep.get('path', '/')}` — {ep.get('description', '')}")
                lines.append("")

        # Non-functional requirements
        nfr = prd.get("non_functional_requirements", {})
        if nfr:
            lines.append("## 5. Non-Functional Requirements")
            lines.append("")
            for category, reqs in nfr.items():
                lines.append(f"### {category.title()}")
                for req in reqs:
                    lines.append(f"- {req}")
                lines.append("")

        # Implementation roadmap
        roadmap = prd.get("implementation_roadmap", {})
        if roadmap:
            lines.append("## 6. Implementation Roadmap")
            lines.append("")
            lines.append(f"**MVP Scope:** {roadmap.get('mvp_scope', '')}")
            lines.append("")
            for phase in roadmap.get("phases", []):
                lines.append(f"### {phase['name']}")
                lines.append(f"{phase.get('description', '')}")
                if phase.get("epics"):
                    lines.append(f"_Epics:_ {', '.join(phase['epics'])}")
                lines.append("")

        lines.append("---")
        lines.append("*Generated by JD Automation System*")

        return "\n".join(lines)
