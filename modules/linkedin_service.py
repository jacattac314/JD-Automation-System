"""
LinkedIn Integration Module.

Creates LinkedIn project entries via API.
"""

import requests
from loguru import logger
from typing import Dict, Any

from core.config import config


class LinkedInService:
    """Manages LinkedIn profile project integration."""
    
    API_BASE = "https://api.linkedin.com/v2"
    
    def __init__(self):
        if not config.linkedin_access_token:
            logger.warning("LinkedIn access token not configured")
        
        self.access_token = config.linkedin_access_token
    
    def create_project(self, title: str, description: str, url: str) -> Dict[str, Any]:
        """
        Create a project entry on LinkedIn profile.
        
        Args:
            title: Project title
            description: Project description
            url: GitHub repository URL
            
        Returns:
            Result dictionary with status and project ID
        """
        if not self.access_token:
            logger.warning("Skipping LinkedIn integration - no token configured")
            return {"status": "skipped", "reason": "No access token"}
        
        logger.info(f"Creating LinkedIn project: {title}")
        
        endpoint = f"{self.API_BASE}/projects"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        payload = {
            "title": title,
            "description": description,
            "url": url,
            # Note: Actual LinkedIn API payload structure may vary
            # This is a simplified version based on typical REST API patterns
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 201:
                logger.info("LinkedIn project created successfully")
                return {
                    "status": "success",
                    "project_id": response.headers.get("X-RestLi-Id"),
                    "message": "Project added to LinkedIn profile"
                }
            else:
                logger.error(f"LinkedIn API error: {response.status_code} - {response.text}")
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "message": response.text
                }
                
        except requests.RequestException as e:
            logger.error(f"LinkedIn API request failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def verify_token(self) -> bool:
        """Verify LinkedIn access token is valid."""
        if not self.access_token:
            return False
        
        endpoint = f"{self.API_BASE}/me"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
