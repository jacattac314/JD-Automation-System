"""
JD Automation System - Main Package
"""

__version__ = "0.1.0"
__author__ = "JD Automation Team"
__description__ = "Local-First Job Description to Project Automation System"

from core.orchestrator import Orchestrator
from core.config import config

__all__ = ["Orchestrator", "config"]
