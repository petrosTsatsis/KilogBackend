import logging
from typing import Optional

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import User
from app.services import user_service

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Cache the JWKS client to avoid repeated network calls
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    """
    Get or create a cached JWKS client for Clerk token verification.
    Returns None if CLERK_FRONTEND_API is not configured.
    """
    global _jwks_client
    if _jwks_client is None:
        clerk_frontend_api = settings.CLERK_FRONTEND_API
        if not clerk_frontend_api:
            return None

        jwks_url = f"https://{clerk_frontend_api}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)

    return _jwks_client


def verify_clerk_jwt(token: str) -> dict:
    """
    Verify the Clerk JWT token and return the decoded payload.

    Uses JWKS verification if CLERK_FRONTEND_API is configured,
    otherwise falls back to using the PEM key from JWT_KEY.

    Validates:
    - Token signature
    - Token expiration (exp claim)
    - Token not-before time (nbf claim)

    Raises HTTPException if verification fails.
    """
    try:
        jwks_client = get_jwks_client()

        if jwks_client:
            # Use JWKS for verification (preferred method)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "require": ["sub", "exp", "nbf"]
                }
            )
        else:
            # Fallback: use the PEM key from settings.JWT_KEY
            # This key should be the Clerk PEM public key
            decoded = jwt.decode(
                token,
                settings.JWT_KEY,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "require": ["sub", "exp", "nbf"]
                }
            )

        return decoded

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"Error verifying Clerk token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Extracts the Clerk user ID from the verified JWT and finds the corresponding internal user.
    """
    token = credentials.credentials

    # Verify the JWT and extract claims
    decoded = verify_clerk_jwt(token)
    clerk_user_id = decoded.get("sub")

    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )

    # Find the internal user by Clerk auth_id
    user = user_service.get_user_by_auth_id(db, clerk_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
