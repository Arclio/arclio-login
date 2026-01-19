"""Kinde OAuth client for browser-based authentication."""

import base64
import json
import os
import secrets
from typing import Optional

import httpx

from .types import KindeTokens, KindeUser


class KindeClient:
    """OAuth client for Kinde authentication."""

    def __init__(
        self,
        domain: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.domain = domain or os.getenv("KINDE_AUTH_DOMAIN") or os.getenv("KINDE_DOMAIN") or ""
        self.client_id = client_id or os.getenv("KINDE_CLIENT_ID") or ""
        self.client_secret = client_secret or os.getenv("KINDE_CLIENT_SECRET") or ""

    def is_configured(self) -> bool:
        """Check if client has required configuration."""
        return bool(self.domain and self.client_id and self.client_secret)

    def build_auth_url(self, redirect_uri: str) -> str:
        """Build OAuth authorization URL."""
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid profile email offline",
            "state": state,
            "nonce": nonce,
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.domain}/oauth2/auth?{query}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> KindeTokens:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.domain}/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error_description") or error_data.get("error")
                except Exception:
                    error_msg = response.text
                raise Exception(f"Token exchange failed: {error_msg}")

            data = response.json()
            return KindeTokens(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                id_token=data.get("id_token"),
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in", 3600),
            )

    async def refresh_token(self, refresh_token: str) -> KindeTokens:
        """Refresh access token using refresh token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.domain}/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error_description") or error_data.get("error")
                except Exception:
                    error_msg = response.text
                raise Exception(f"Token refresh failed: {error_msg}")

            data = response.json()
            return KindeTokens(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token") or refresh_token,
                id_token=data.get("id_token"),
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in", 3600),
            )

    async def get_user_info(self, access_token: str) -> KindeUser:
        """Get user info from access token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.domain}/oauth2/v2/user_profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 200:
                data = response.json()
                return KindeUser(
                    sub=data["sub"],
                    email=data.get("email"),
                    given_name=data.get("given_name"),
                    family_name=data.get("family_name"),
                    picture=data.get("picture"),
                )

            # Fallback: decode JWT to get basic info
            return self._decode_token(access_token)

    def _decode_token(self, token: str) -> KindeUser:
        """Decode JWT token to extract user info (without verification)."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")

            # Decode payload (add padding if needed)
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            payload = json.loads(base64.urlsafe_b64decode(payload_b64))

            return KindeUser(
                sub=payload.get("sub", ""),
                email=payload.get("email"),
                given_name=payload.get("given_name"),
                family_name=payload.get("family_name"),
                picture=payload.get("picture"),
            )
        except Exception as e:
            raise Exception(f"Failed to decode JWT token: {e}")


# Singleton instance (lazy-initialized)
_kinde_client: Optional[KindeClient] = None


def get_kinde_client() -> KindeClient:
    """Get or create singleton KindeClient instance."""
    global _kinde_client
    if _kinde_client is None:
        _kinde_client = KindeClient()
    return _kinde_client
