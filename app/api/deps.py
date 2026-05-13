from __future__ import annotations

from __future__ import annotations

from functools import lru_cache

import requests
from fastapi import Header, HTTPException, status
from jose import jwk, jwt
from jose.utils import base64url_decode

from app.core.config import get_settings

__all__ = ["get_settings", "get_current_user"]


@lru_cache(maxsize=1)
def get_jwks() -> list[dict]:
    """Fetch and cache Clerk's JWKS keys."""
    settings = get_settings()
    if not settings.clerk_jwks_url:
        return []
    resp = requests.get(settings.clerk_jwks_url, timeout=10)
    resp.raise_for_status()
    return resp.json().get("keys", [])


def verify_clerk_token(token: str) -> str:
    """Verify a Clerk JWT and return the user_id (sub claim)."""
    keys = get_jwks()
    if not keys:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWKS not configured",
        )

    # Get unverified header to find the matching key
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    # Find the matching key
    key_data = None
    for k in keys:
        if k.get("kid") == kid:
            key_data = k
            break

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: key not found",
        )

    # Construct the public key
    public_key = jwk.construct(key_data)

    # Decode and verify
    message_str, encoded_sig_str = token.rsplit(".", 1)
    message = message_str.encode("utf-8")
    encoded_sig = encoded_sig_str.encode("utf-8")
    decoded_sig = base64url_decode(encoded_sig)

    if not public_key.verify(message, decoded_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: signature mismatch",
        )

    # Decode the payload (without verification, we already verified the signature)
    payload = jwt.get_unverified_claims(token)

    # Verify expiration
    import time
    exp = payload.get("exp", 0)
    if exp < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no subject",
        )

    return user_id


def get_current_user(authorization: str = Header(...)) -> str:
    """FastAPI dependency that extracts and validates the Clerk JWT.
    Returns the user_id string."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    token = authorization.split("Bearer ")[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )
    return verify_clerk_token(token)
