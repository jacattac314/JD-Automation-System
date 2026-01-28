"""
Authentication module for GitHub OAuth and JWT token management.

Flow:
1. User clicks "Sign in with GitHub" -> redirected to GitHub OAuth page
2. GitHub redirects back with authorization code
3. Server exchanges code for GitHub access token
4. Server creates/updates user, encrypts GitHub token, issues JWT
5. Frontend stores JWT, sends it with all API requests
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
import requests
from cryptography.fernet import Fernet
from fastapi import HTTPException, Depends, Request
from loguru import logger

from core.settings import settings


# ============ Token Encryption ============

def _get_fernet() -> Fernet:
    """Get Fernet instance for encrypting GitHub tokens at rest."""
    # Derive a Fernet key from the JWT secret (must be 32 url-safe base64 bytes)
    import hashlib
    import base64
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.jwt_secret.encode()).digest()
    )
    return Fernet(key)


def encrypt_token(token: str) -> str:
    """Encrypt a GitHub access token for database storage."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decrypt a stored GitHub access token."""
    return _get_fernet().decrypt(encrypted.encode()).decode()


# ============ JWT Management ============

def create_jwt(user_id: int, github_username: str) -> str:
    """Create a JWT access token for the authenticated user."""
    payload = {
        "sub": str(user_id),
        "username": github_username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token.

    Returns:
        Dict with 'sub' (user_id as string) and 'username'

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============ GitHub OAuth ============

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


def get_github_authorize_url(redirect_uri: str) -> str:
    """Generate the GitHub OAuth authorization URL."""
    if not settings.github_client_id:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured (GITHUB_CLIENT_ID missing)"
        )
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": redirect_uri,
        "scope": "repo user:email",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GITHUB_AUTHORIZE_URL}?{query}"


def exchange_code_for_token(code: str) -> str:
    """Exchange GitHub OAuth authorization code for access token.

    Returns:
        GitHub access token string

    Raises:
        HTTPException: If the exchange fails
    """
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured"
        )

    response = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    data = response.json()
    token = data.get("access_token")
    if not token:
        error = data.get("error_description", data.get("error", "Unknown error"))
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error}")

    return token


def get_github_user(access_token: str) -> Dict[str, Any]:
    """Fetch the authenticated GitHub user's profile.

    Returns:
        Dict with id, login, avatar_url, email
    """
    response = requests.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to fetch GitHub user profile")

    user_data = response.json()
    return {
        "id": user_data["id"],
        "login": user_data["login"],
        "avatar_url": user_data.get("avatar_url"),
        "email": user_data.get("email"),
    }


# ============ FastAPI Dependencies ============

def get_current_user_token(request: Request) -> Dict[str, Any]:
    """FastAPI dependency: extract and validate JWT from Authorization header.

    Returns:
        Decoded JWT payload with 'sub' and 'username'

    Raises:
        HTTPException 401: If no token or invalid token
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]  # Strip "Bearer "
    return decode_jwt(token)


def require_auth(token_data: Dict[str, Any] = Depends(get_current_user_token)) -> Dict[str, Any]:
    """FastAPI dependency: require authentication. Returns JWT payload."""
    return token_data


def optional_auth(request: Request) -> Optional[Dict[str, Any]]:
    """FastAPI dependency: optional authentication. Returns JWT payload or None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    try:
        return decode_jwt(auth_header[7:])
    except HTTPException:
        return None
