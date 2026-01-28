"""
Gemini Client Module.

Generates enhanced app descriptions and comprehensive PRDs using Google's Gemini AI.
"""

import json
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
from loguru import logger
from typing import Dict, List, Any, Optional


from core.config import config


class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        auth_key = api_key or config.gemini_api_key
        
        # We don't raise error here to allow fallback usage even without key
        if auth_key and HAS_GENAI:
            try:
                genai.configure(api_key=auth_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.configured = True
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")
                self.configured = False
        else:
            self.configured = False


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

        if not self.configured or not self.model:
            logger.info("Gemini not configured, using fallback")
            return self._generate_fallback_enhanced_idea(app_idea, tech_preferences)

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

        if not self.configured or not self.model:
            logger.info("Gemini not configured, using fallback")
            prd_data = self._generate_fallback_prd(enhanced_idea)
            return {
                "prd": prd_data,
                "prd_markdown": self._prd_to_markdown(prd_data, enhanced_idea)
            }

        try:
            response = self.model.generate_content(prompt)
            text = response.text

            # Try to parse structured JSON from the response
            prd_data = self._parse_json_response(text)
            if prd_data and "epics" in prd_data:
                # Validate and refine the PRD structure
                prd_data = self._validate_and_refine_prd(prd_data, enhanced_idea)
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

        return f"""You are a senior product strategist with deep technical expertise. A user has provided a rough application idea.
Your job is to enhance it into a clear, structured product concept that an AI coding agent can implement autonomously.

**User's raw idea:**
{app_idea}
{tech_section}

**Return ONLY valid JSON** with this exact structure (no markdown, no extra text):
{{
  "title": "A concise, professional project name (2-5 words, suitable as a repo name)",
  "description": "2-3 paragraph detailed description covering: (1) what the application does and its core workflow, (2) key technical capabilities and integrations, (3) why it matters and what differentiates it",
  "target_users": "2-3 specific user personas with their roles, goals, and pain points. Example: 'Small business owners (5-50 employees) who currently track inventory in spreadsheets and need real-time stock visibility across multiple locations'",
  "problem_statement": "A specific, measurable problem statement. Include: who is affected, what they currently do, why it fails, and the cost of the problem. Avoid vague statements like 'users need a better way'",
  "key_value_props": ["Specific, measurable value prop 1", "Specific, measurable value prop 2", "Specific, measurable value prop 3"],
  "suggested_tech_stack": {{
    "frontend": ["specific framework with version context, e.g. 'Next.js 14 (App Router)'", "supporting libraries"],
    "backend": ["specific framework, e.g. 'FastAPI with async support'", "supporting libraries"],
    "database": ["specific database with justification, e.g. 'PostgreSQL (relational data with JSON support)'"],
    "infrastructure": ["deployment target", "containerization", "CI/CD"]
  }}
}}

**Quality requirements:**
- Technology choices must include brief justification (why this tech for this use case)
- Description must mention specific data flows and user interactions, not just abstract capabilities
- Value propositions must be concrete and measurable (e.g., "Reduces inventory reconciliation from 4 hours to 5 minutes" not "Saves time")
- The output will be used to generate a detailed PRD with API specs, data models, and acceptance criteria

**Example of GOOD output (for reference only -- do not copy):**
{{
  "title": "FleetPulse",
  "description": "FleetPulse is a real-time fleet management platform that tracks vehicle locations, monitors driver behavior, and optimizes delivery routes using GPS telemetry data. The system ingests position data from OBD-II devices via MQTT, processes it through a geofencing engine, and surfaces actionable insights through a map-based dashboard. It integrates with existing dispatch systems via REST APIs and sends automated alerts for speeding, unauthorized use, and maintenance schedules. FleetPulse differentiates from competitors by offering sub-second position updates and ML-powered route optimization that adapts to real-time traffic conditions.",
  "target_users": "Logistics managers at mid-size delivery companies (50-500 vehicles) who currently rely on phone calls and manual check-ins to track drivers, leading to missed deliveries and fuel waste",
  "problem_statement": "Delivery companies with 50-500 vehicles lose an average of 15% fuel costs to inefficient routing and have no visibility into real-time driver behavior, resulting in 8-12% late deliveries and $50K+ annual insurance premium increases from preventable incidents",
  "key_value_props": ["Reduce fuel costs 12-18% through ML-optimized routing", "Cut late deliveries by 60% with real-time ETA updates and proactive rerouting", "Lower insurance premiums 15-20% with documented driver safety improvements"],
  "suggested_tech_stack": {{
    "frontend": ["Next.js 14 (App Router for SSR map rendering)", "Mapbox GL JS (vector tile maps with real-time layers)", "TanStack Query (real-time data synchronization)"],
    "backend": ["FastAPI with async support (high-throughput telemetry ingestion)", "Celery (background route optimization tasks)", "MQTT broker via Eclipse Mosquitto (IoT device communication)"],
    "database": ["PostgreSQL with PostGIS (spatial queries for geofencing)", "TimescaleDB extension (time-series telemetry data)", "Redis (real-time position cache and pub/sub)"],
    "infrastructure": ["Docker Compose (local dev)", "AWS ECS Fargate (production)", "GitHub Actions (CI/CD)"]
  }}
}}

Be specific and practical. Vague, generic output is not acceptable."""

    def _build_prd_prompt(self, enhanced_idea: Dict[str, Any]) -> str:
        """Build prompt for PRD generation."""
        return f"""You are a senior technical product manager creating a comprehensive Product Requirements Document (PRD).
This PRD will be given directly to an AI coding agent (Claude Code) that will autonomously implement every feature.
The quality of the PRD determines whether the AI can build the project successfully -- vague specs produce broken code.

**Application Concept:**
Title: {enhanced_idea.get('title', 'Untitled')}
Description: {enhanced_idea.get('description', '')}
Target Users: {enhanced_idea.get('target_users', 'General users')}
Problem Statement: {enhanced_idea.get('problem_statement', '')}
Key Value Props: {json.dumps(enhanced_idea.get('key_value_props', []))}
Suggested Tech Stack: {json.dumps(enhanced_idea.get('suggested_tech_stack', {}))}

**Return ONLY valid JSON** with this exact structure (no markdown, no extra text):
{{
  "product_overview": {{
    "vision": "1-2 sentence product vision tied to the problem statement",
    "goals": ["Specific, measurable goal 1", "Goal 2", "Goal 3"],
    "success_metrics": ["Quantifiable metric 1", "Metric 2"]
  }},
  "epics": [
    {{
      "name": "Epic Name",
      "description": "What this epic covers and WHY it's needed",
      "priority": "P0",
      "depends_on": [],
      "user_stories": [
        {{
          "title": "User Story Title",
          "story": "As a [specific persona], I want [specific action with details] so that [measurable benefit]",
          "acceptance_criteria": [
            "Given [specific precondition with data], when [specific user action], then [specific observable outcome with exact behavior]"
          ],
          "features": [
            {{
              "name": "Feature name (verb + noun, e.g. 'Create user registration form')",
              "description": "Detailed implementation spec: what files to create, what logic to implement, what inputs/outputs to expect. Must be specific enough for a developer to implement without asking questions.",
              "complexity": "S",
              "depends_on": []
            }}
          ]
        }}
      ]
    }}
  ],
  "technical_architecture": {{
    "overview": "High-level architecture description including data flow between components",
    "components": ["Component 1 -- what it does and what framework/library implements it", "Component 2"],
    "data_model": [
      {{
        "entity": "EntityName",
        "fields": ["id: UUID (PK)", "name: VARCHAR(255) NOT NULL", "email: VARCHAR(255) UNIQUE NOT NULL", "created_at: TIMESTAMP DEFAULT NOW()"],
        "relationships": "EntityName belongs_to OtherEntity via other_entity_id (FK). EntityName has_many Items.",
        "indexes": ["idx_entity_email ON email", "idx_entity_created ON created_at"]
      }}
    ],
    "api_endpoints": [
      {{
        "method": "POST",
        "path": "/api/v1/resource",
        "description": "Creates a new resource",
        "request_body": {{"name": "string (required)", "email": "string (required, valid email)"}},
        "response": {{"201": "Resource created with id, name, email, created_at", "400": "Validation error with field-level messages", "409": "Email already exists"}},
        "auth": "Required -- Bearer JWT token"
      }}
    ]
  }},
  "non_functional_requirements": {{
    "performance": ["API response time < 200ms for 95th percentile under 100 concurrent users", "Page load time < 2s on 3G connection"],
    "security": ["All passwords hashed with bcrypt (cost factor 12)", "JWT tokens expire after 24 hours with refresh token rotation", "All user inputs sanitized against XSS and SQL injection", "CORS restricted to specific origins"],
    "scalability": ["Stateless API design for horizontal scaling", "Database connection pooling (max 20 connections per instance)"],
    "error_handling": ["All API errors return consistent JSON format: {{error: string, code: string, details: object}}", "Client-side form validation mirrors server-side validation", "Graceful degradation when external services are unavailable"]
  }},
  "implementation_roadmap": {{
    "mvp_scope": "Specific description of what's in MVP vs what's deferred",
    "phases": [
      {{
        "name": "Phase 1: Foundation",
        "epics": ["Epic Name"],
        "description": "What this phase covers and what's deployable at the end"
      }}
    ]
  }}
}}

**CRITICAL REQUIREMENTS -- read carefully:**

1. **Create 4-6 epics** with 3-5 user stories each. Each story has 2-4 acceptance criteria and 1-3 features.

2. **Epic ordering and dependencies:**
   - First epic MUST be "Project Setup & Infrastructure" (P0) -- project scaffolding, dependency installation, database setup, config management
   - Second epic MUST be "Authentication & Authorization" (P0) if the app has users -- registration, login, JWT, protected routes
   - Remaining epics cover domain-specific features in logical build order
   - Use the `depends_on` field to specify which epics/features must be built first

3. **Feature descriptions must be implementation-ready:**
   - BAD: "Implement user management" (too vague -- what files? what logic? what UI?)
   - GOOD: "Create POST /api/v1/users endpoint that accepts {{email, password, name}}, validates email format and password strength (min 8 chars, 1 uppercase, 1 number), hashes password with bcrypt, stores in users table, returns 201 with user object (excluding password) or 400 with validation errors"
   - Each feature should be completable in a single coding session (1-4 files changed)

4. **Acceptance criteria must be testable:**
   - BAD: "Users can log in" (not testable -- what constitutes success?)
   - GOOD: "Given a registered user with email 'test@example.com' and password 'ValidPass1', when they POST to /api/v1/auth/login with those credentials, then they receive a 200 response containing a JWT access_token (expires in 24h) and a refresh_token"

5. **Data model must include:**
   - All fields with SQL-compatible types and constraints (NOT NULL, UNIQUE, DEFAULT, FK)
   - Explicit relationships (belongs_to, has_many, many_to_many with junction table)
   - Indexes for frequently queried fields

6. **API endpoints must include:**
   - Request body schema with field types and validation rules
   - All response status codes with response body descriptions
   - Authentication requirements (public, authenticated, admin-only)

7. **Complexity guidelines:**
   - S (Small): Single file change, < 50 lines of code. Examples: add a config value, create a simple utility function, add a static page
   - M (Medium): 2-3 files changed, 50-200 lines. Examples: create a CRUD endpoint with validation, build a form component with client-side validation
   - L (Large): 4+ files, 200+ lines, involves multiple system interactions. Examples: implement OAuth flow, build real-time WebSocket feature, create complex data pipeline"""

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

    # ---- PRD validation and refinement ----

    def _validate_and_refine_prd(self, prd_data: Dict[str, Any], enhanced_idea: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate PRD structure and attempt AI-powered refinement for weak areas.

        Checks for common quality issues and calls Gemini to fix them if possible.
        Falls back to structural fixes if AI refinement fails.
        """
        issues = self._find_prd_issues(prd_data)

        if not issues:
            logger.info("PRD validation passed -- no issues found")
            return prd_data

        logger.warning(f"PRD validation found {len(issues)} issues: {', '.join(issues)}")

        # Try AI-powered refinement
        if self.configured and self.model:
            try:
                refined = self._ai_refine_prd(prd_data, issues, enhanced_idea)
                if refined and "epics" in refined:
                    logger.info("PRD refined successfully by AI")
                    return refined
            except Exception as e:
                logger.warning(f"AI refinement failed, applying structural fixes: {e}")

        # Apply structural fixes as fallback
        return self._apply_structural_fixes(prd_data)

    def _find_prd_issues(self, prd_data: Dict[str, Any]) -> List[str]:
        """Identify quality issues in the PRD."""
        issues = []

        epics = prd_data.get("epics", [])
        if len(epics) < 3:
            issues.append("too_few_epics")

        # Check for vague feature descriptions (< 30 chars is almost certainly too vague)
        vague_features = 0
        total_features = 0
        for epic in epics:
            for story in epic.get("user_stories", []):
                for feat in story.get("features", []):
                    total_features += 1
                    desc = feat.get("description", "")
                    if len(desc) < 30:
                        vague_features += 1

        if total_features > 0 and vague_features / total_features > 0.3:
            issues.append("vague_feature_descriptions")

        # Check for missing acceptance criteria
        stories_without_ac = 0
        total_stories = 0
        for epic in epics:
            for story in epic.get("user_stories", []):
                total_stories += 1
                ac = story.get("acceptance_criteria", [])
                if len(ac) < 2:
                    stories_without_ac += 1

        if total_stories > 0 and stories_without_ac / total_stories > 0.3:
            issues.append("insufficient_acceptance_criteria")

        # Check for missing technical architecture
        arch = prd_data.get("technical_architecture", {})
        if not arch.get("data_model") or len(arch.get("data_model", [])) == 0:
            issues.append("missing_data_model")
        if not arch.get("api_endpoints") or len(arch.get("api_endpoints", [])) == 0:
            issues.append("missing_api_endpoints")

        # Check for missing dependencies
        has_dependencies = any(
            epic.get("depends_on") or any(
                feat.get("depends_on")
                for story in epic.get("user_stories", [])
                for feat in story.get("features", [])
            )
            for epic in epics
        )
        if not has_dependencies and len(epics) > 2:
            issues.append("missing_dependency_ordering")

        # Check for missing error handling in NFRs
        nfr = prd_data.get("non_functional_requirements", {})
        if not nfr.get("error_handling"):
            issues.append("missing_error_handling_spec")

        return issues

    def _ai_refine_prd(self, prd_data: Dict[str, Any], issues: List[str], enhanced_idea: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use Gemini to refine weak areas of the PRD."""
        issue_descriptions = {
            "too_few_epics": "There are fewer than 3 epics. Add more epics to cover the full scope.",
            "vague_feature_descriptions": "Many feature descriptions are too vague (< 30 chars). Each feature description must specify: what files to create, what logic to implement, what inputs/outputs to expect, and be detailed enough for an AI coding agent to implement without asking questions.",
            "insufficient_acceptance_criteria": "Many user stories have fewer than 2 acceptance criteria. Each story needs 2-4 specific, testable criteria in Given/When/Then format with concrete data examples.",
            "missing_data_model": "The technical architecture is missing a data model. Add all entities with SQL-typed fields, constraints (NOT NULL, UNIQUE, FK), relationships, and indexes.",
            "missing_api_endpoints": "The technical architecture is missing API endpoints. Add all endpoints with method, path, request body schema, response status codes, and auth requirements.",
            "missing_dependency_ordering": "Epics and features have no dependency ordering. Add 'depends_on' arrays specifying which epics/features must be built first.",
            "missing_error_handling_spec": "Non-functional requirements are missing error handling specifications. Add a consistent error response format, client-side validation rules, and graceful degradation strategies."
        }

        issue_text = "\n".join(f"- {issue_descriptions.get(i, i)}" for i in issues)

        prompt = f"""You are a senior technical product manager reviewing a PRD that has quality issues.
Fix ONLY the identified issues while preserving all existing good content.

**Application:** {enhanced_idea.get('title', 'Application')}

**Current PRD (JSON):**
{json.dumps(prd_data, indent=2)[:8000]}

**Issues to fix:**
{issue_text}

Return ONLY the complete corrected PRD as valid JSON. Preserve the exact same structure.
Keep all existing content that is already good -- only improve the weak areas listed above.
Do NOT remove any existing epics, stories, or features -- only enhance them or add missing elements."""

        response = self.model.generate_content(prompt)
        return self._parse_json_response(response.text)

    def _apply_structural_fixes(self, prd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply basic structural fixes to the PRD without AI."""
        # Ensure all epics have depends_on
        epics = prd_data.get("epics", [])
        for i, epic in enumerate(epics):
            if "depends_on" not in epic:
                epic["depends_on"] = [epics[0]["name"]] if i > 0 else []

            for story in epic.get("user_stories", []):
                for feat in story.get("features", []):
                    if "depends_on" not in feat:
                        feat["depends_on"] = []

        # Ensure NFRs have error_handling
        nfr = prd_data.setdefault("non_functional_requirements", {})
        if "error_handling" not in nfr:
            nfr["error_handling"] = [
                "All API errors return consistent JSON: {\"error\": \"message\", \"code\": \"ERROR_CODE\", \"details\": {}}",
                "Client-side form validation mirrors server-side rules",
                "Network failures show user-friendly retry prompts"
            ]

        # Ensure technical architecture has at least empty structures
        arch = prd_data.setdefault("technical_architecture", {})
        if not arch.get("data_model"):
            arch["data_model"] = []
        if not arch.get("api_endpoints"):
            arch["api_endpoints"] = []

        return prd_data

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
        """Generate a domain-aware PRD structure if API fails.

        Analyzes the enhanced idea to create relevant epics and features
        instead of generic placeholders.
        """
        title = enhanced_idea.get("title", "Application")
        description = enhanced_idea.get("description", "")
        target_users = enhanced_idea.get("target_users", "end users")
        tech_stack = enhanced_idea.get("suggested_tech_stack", {})
        value_props = enhanced_idea.get("key_value_props", [])

        # Determine domain characteristics from the description
        desc_lower = description.lower()
        has_auth = any(w in desc_lower for w in ["user", "login", "account", "auth", "register", "profile"])
        has_api = any(w in desc_lower for w in ["api", "endpoint", "rest", "backend", "server"])
        has_data = any(w in desc_lower for w in ["data", "database", "store", "save", "record", "track"])
        has_dashboard = any(w in desc_lower for w in ["dashboard", "analytics", "report", "chart", "metric", "monitor"])
        has_realtime = any(w in desc_lower for w in ["real-time", "realtime", "live", "stream", "notification", "websocket"])

        # Build tech-specific foundation features
        frontend_tech = tech_stack.get("frontend", ["React"])[0] if tech_stack.get("frontend") else "React"
        backend_tech = tech_stack.get("backend", ["Python"])[0] if tech_stack.get("backend") else "Python"
        db_tech = tech_stack.get("database", ["PostgreSQL"])[0] if tech_stack.get("database") else "PostgreSQL"

        # Build domain-specific epics
        epics = [
            {
                "name": "Project Setup & Infrastructure",
                "description": f"Initialize {title} with {backend_tech} backend, {frontend_tech} frontend, and {db_tech} database. Establish project structure, dependency management, and development tooling.",
                "priority": "P0",
                "depends_on": [],
                "user_stories": [
                    {
                        "title": "Project Initialization",
                        "story": f"As a developer, I want a properly scaffolded {backend_tech} + {frontend_tech} project so that I can begin feature development immediately",
                        "acceptance_criteria": [
                            f"Given a clean checkout, when I run the install command, then all dependencies install without errors",
                            f"Given the project is set up, when I run the dev server, then both frontend and backend start and are accessible",
                            f"Given the project structure, when I check the directory layout, then it follows {backend_tech} best practices with separate src/, tests/, and config/ directories"
                        ],
                        "features": [
                            {"name": f"Scaffold {backend_tech} project", "description": f"Create {backend_tech} project with proper directory structure (src/, tests/, config/), dependency file (requirements.txt or package.json), and development server configuration", "complexity": "S", "depends_on": []},
                            {"name": f"Configure {db_tech} connection", "description": f"Set up {db_tech} database connection with connection pooling, environment-based configuration (DATABASE_URL), and a health check query. Create migration tooling.", "complexity": "M", "depends_on": []},
                            {"name": "Environment configuration", "description": "Create .env.example with all required variables, config loader that validates required vars on startup, and separate dev/production settings", "complexity": "S", "depends_on": []}
                        ]
                    }
                ]
            }
        ]

        # Add auth epic if the app involves users
        if has_auth:
            epics.append({
                "name": "Authentication & User Management",
                "description": f"User registration, login, and session management for {title}",
                "priority": "P0",
                "depends_on": ["Project Setup & Infrastructure"],
                "user_stories": [
                    {
                        "title": "User Registration",
                        "story": f"As a new {target_users.split('.')[0].split(',')[0]}, I want to create an account so that I can access {title}",
                        "acceptance_criteria": [
                            "Given a valid email and password (min 8 chars, 1 uppercase, 1 number), when I submit the registration form, then my account is created and I receive a confirmation",
                            "Given an email that already exists, when I try to register, then I see an error message 'An account with this email already exists'",
                            "Given an invalid password, when I submit registration, then I see specific validation errors listing which requirements are not met"
                        ],
                        "features": [
                            {"name": "Create user registration endpoint", "description": f"POST /api/v1/auth/register accepting {{email, password, name}}. Validate email format, password strength, hash with bcrypt, store in users table, return 201 with user object (excluding password) or 400/409 with errors", "complexity": "M", "depends_on": []},
                            {"name": "Create login endpoint", "description": "POST /api/v1/auth/login accepting {email, password}. Verify credentials, return JWT access_token (24h expiry) and refresh_token, or 401 for invalid credentials", "complexity": "M", "depends_on": []},
                            {"name": "Build registration and login UI", "description": f"Create registration and login forms with {frontend_tech}. Client-side validation mirroring server rules. Show field-level errors. Redirect to dashboard on success.", "complexity": "M", "depends_on": []}
                        ]
                    }
                ]
            })

        # Core features epic -- derived from the description
        core_description = f"Implement the primary functionality of {title}: {description[:150]}"
        core_features = []
        if has_api:
            core_features.append({"name": "Build core API endpoints", "description": f"Create RESTful API endpoints for the main domain resources described in the application concept. Include proper request validation, error handling, and response formatting.", "complexity": "L", "depends_on": []})
        if has_dashboard:
            core_features.append({"name": "Build dashboard view", "description": f"Create a dashboard page with {frontend_tech} showing key metrics, recent activity, and quick actions. Use responsive card-based layout with loading states.", "complexity": "L", "depends_on": []})
        if has_realtime:
            core_features.append({"name": "Add real-time updates", "description": "Implement WebSocket connection for live data updates. Include connection management (auto-reconnect on disconnect), event handling, and UI state synchronization.", "complexity": "L", "depends_on": []})

        # Always have at least two core features
        if len(core_features) == 0:
            core_features = [
                {"name": f"Implement main {title} workflow", "description": f"Build the primary user workflow: {description[:100]}. Create the necessary API endpoints, service logic, and UI components.", "complexity": "L", "depends_on": []},
                {"name": f"Build {title} user interface", "description": f"Create the main UI views with {frontend_tech}. Include navigation, primary content area, and responsive layout. Connect to backend APIs.", "complexity": "L", "depends_on": []}
            ]

        core_ac = [
            f"Given a logged-in user, when they access the main {title} interface, then they see the primary functionality as described in the product concept",
            "Given valid input data, when the user performs the core action, then the system processes it correctly and provides confirmation",
            "Given an error occurs during processing, when the user sees the result, then a clear error message is shown with a retry option"
        ]

        epics.append({
            "name": "Core Features",
            "description": core_description,
            "priority": "P0",
            "depends_on": ["Project Setup & Infrastructure"] + (["Authentication & User Management"] if has_auth else []),
            "user_stories": [
                {
                    "title": f"Primary {title} Functionality",
                    "story": f"As a {target_users.split('.')[0].split(',')[0]}, I want to use the core features of {title} so that I can {value_props[0].lower() if value_props else 'accomplish my goals'}",
                    "acceptance_criteria": core_ac,
                    "features": core_features
                }
            ]
        })

        # Data management epic
        if has_data:
            epics.append({
                "name": "Data Management",
                "description": f"Data storage, retrieval, and management for {title} using {db_tech}",
                "priority": "P1",
                "depends_on": ["Project Setup & Infrastructure", "Core Features"],
                "user_stories": [
                    {
                        "title": "Data Persistence & Retrieval",
                        "story": f"As a user, I want my data to be saved and retrievable so that I don't lose my work",
                        "acceptance_criteria": [
                            f"Given new data is submitted, when I check the {db_tech} database, then the data is persisted with correct types and constraints",
                            "Given existing data, when I request it via the API, then I receive properly formatted JSON with pagination support",
                            "Given a data update, when I submit changes, then only the changed fields are updated and the updated_at timestamp reflects the change"
                        ],
                        "features": [
                            {"name": f"Create {db_tech} schema and migrations", "description": f"Define database tables with proper field types, constraints (NOT NULL, UNIQUE, FK), indexes, and create migration scripts", "complexity": "M", "depends_on": []},
                            {"name": "Build data access layer", "description": "Create repository/service classes with CRUD operations, query builders, and pagination. Include input validation at the service layer.", "complexity": "M", "depends_on": []},
                            {"name": "Add data export functionality", "description": "Create GET /api/v1/export endpoint that returns data in JSON or CSV format. Include date range filtering and field selection.", "complexity": "S", "depends_on": []}
                        ]
                    }
                ]
            })

        # Testing epic
        epics.append({
            "name": "Testing & Quality Assurance",
            "description": f"Automated testing suite for {title} covering unit, integration, and end-to-end tests",
            "priority": "P1",
            "depends_on": ["Core Features"],
            "user_stories": [
                {
                    "title": "Automated Test Suite",
                    "story": "As a developer, I want comprehensive automated tests so that I can refactor and deploy with confidence",
                    "acceptance_criteria": [
                        "Given the test suite, when I run the test command, then all tests pass with > 70% code coverage on core modules",
                        "Given a failing test, when I review the output, then the error message clearly indicates what failed and why",
                        "Given the CI pipeline, when I push code, then tests run automatically and block merge on failure"
                    ],
                    "features": [
                        {"name": "Write unit tests for core services", "description": "Create unit tests for all service/business logic classes. Mock external dependencies (database, APIs). Test happy path and error cases.", "complexity": "M", "depends_on": []},
                        {"name": "Write API integration tests", "description": "Create integration tests for all API endpoints using test client. Test request validation, authentication, success responses, and error handling.", "complexity": "M", "depends_on": []},
                        {"name": "Configure CI test pipeline", "description": "Set up GitHub Actions workflow that installs dependencies, runs linting, executes test suite, and reports coverage on every push and PR", "complexity": "S", "depends_on": []}
                    ]
                }
            ]
        })

        # Build data model based on detected domain
        data_model = []
        if has_auth:
            data_model.append({
                "entity": "User",
                "fields": ["id: UUID (PK, DEFAULT gen_random_uuid())", "email: VARCHAR(255) UNIQUE NOT NULL", "password_hash: VARCHAR(255) NOT NULL", "name: VARCHAR(255) NOT NULL", "created_at: TIMESTAMP DEFAULT NOW()", "updated_at: TIMESTAMP DEFAULT NOW()"],
                "relationships": "User has_many owned resources",
                "indexes": ["idx_user_email ON email"]
            })

        # Build API endpoints list
        api_endpoints = []
        if has_auth:
            api_endpoints.extend([
                {"method": "POST", "path": "/api/v1/auth/register", "description": "Register new user account", "request_body": {"email": "string (required)", "password": "string (required, min 8)", "name": "string (required)"}, "response": {"201": "User created", "400": "Validation error", "409": "Email exists"}, "auth": "Public"},
                {"method": "POST", "path": "/api/v1/auth/login", "description": "Authenticate and get JWT token", "request_body": {"email": "string (required)", "password": "string (required)"}, "response": {"200": "JWT tokens returned", "401": "Invalid credentials"}, "auth": "Public"}
            ])
        api_endpoints.append(
            {"method": "GET", "path": "/api/v1/health", "description": "Health check endpoint", "response": {"200": "Service healthy with timestamp"}, "auth": "Public"}
        )

        return {
            "product_overview": {
                "vision": f"Build {title} to solve: {enhanced_idea.get('problem_statement', description[:100])}",
                "goals": [
                    value_props[0] if value_props else "Deliver core functionality as described",
                    value_props[1] if len(value_props) > 1 else "Provide a clean, production-ready codebase",
                    value_props[2] if len(value_props) > 2 else "Ensure reliability through automated testing"
                ],
                "success_metrics": [
                    "All core features implemented and passing automated tests",
                    "API response time < 500ms for 95th percentile requests",
                    "Zero critical security vulnerabilities in dependency scan"
                ]
            },
            "epics": epics,
            "technical_architecture": {
                "overview": f"{title} uses a {backend_tech} backend with {frontend_tech} frontend and {db_tech} for data persistence. The architecture follows a layered pattern: API routes → service layer → data access layer → database.",
                "components": [
                    f"{frontend_tech} frontend -- serves the user interface with client-side routing and state management",
                    f"{backend_tech} backend -- RESTful API server handling business logic and data validation",
                    f"{db_tech} database -- persistent storage with migrations and connection pooling",
                    "Configuration -- environment-based settings with .env for local development"
                ],
                "data_model": data_model,
                "api_endpoints": api_endpoints
            },
            "non_functional_requirements": {
                "performance": ["API response time < 500ms for 95th percentile under 50 concurrent users", "Frontend initial page load < 3s on broadband connection"],
                "security": ["All passwords hashed with bcrypt (cost factor 12)", "JWT tokens with 24h expiry", "Input validation on all endpoints", "CORS restricted to allowed origins", "SQL injection prevention via parameterized queries"],
                "scalability": ["Stateless API design for horizontal scaling", "Database connection pooling (max 10 connections per instance)"],
                "error_handling": [
                    "All API errors return consistent JSON: {\"error\": \"message\", \"code\": \"ERROR_CODE\", \"details\": {}}",
                    "Client-side form validation mirrors server-side rules",
                    "Network failures show user-friendly retry prompts",
                    "Unhandled exceptions logged with stack trace and request context"
                ]
            },
            "implementation_roadmap": {
                "mvp_scope": f"Project Setup + {'Authentication + ' if has_auth else ''}Core Features -- minimum viable {title} with essential functionality",
                "phases": [
                    {"name": "Phase 1: Foundation", "epics": ["Project Setup & Infrastructure"] + (["Authentication & User Management"] if has_auth else []), "description": "Project scaffolding, database setup, and user auth. Deployable skeleton with login."},
                    {"name": "Phase 2: Core", "epics": ["Core Features"] + (["Data Management"] if has_data else []), "description": "Primary application features and data persistence. Usable product."},
                    {"name": "Phase 3: Quality", "epics": ["Testing & Quality Assurance"], "description": "Automated test suite, CI pipeline, and production hardening."}
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
            if epic.get("depends_on"):
                lines.append(f"_Depends on: {', '.join(epic['depends_on'])}_")
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
                    lines.append(f"- `[{complexity}]` **{feat['name']}** -- {feat.get('description', '')}")
                    if feat.get("depends_on"):
                        lines.append(f"  - _Depends on: {', '.join(feat['depends_on'])}_")
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
                    auth_tag = f" `[{ep['auth']}]`" if ep.get("auth") else ""
                    lines.append(f"- `{ep.get('method', 'GET')} {ep.get('path', '/')}` -- {ep.get('description', '')}{auth_tag}")
                    if ep.get("request_body"):
                        body_parts = [f"`{k}`: {v}" for k, v in ep["request_body"].items()]
                        lines.append(f"  - Request: {', '.join(body_parts)}")
                    if ep.get("response") and isinstance(ep["response"], dict):
                        for code, desc in ep["response"].items():
                            lines.append(f"  - `{code}`: {desc}")
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
