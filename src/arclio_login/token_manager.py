"""Token management with automatic refresh."""

import asyncio

from . import config
from .kinde_client import get_kinde_client


async def get_valid_token() -> str:
    """Get a valid access token, refreshing if expired."""
    access_token = config.get_access_token()

    if not access_token:
        raise Exception("Not authenticated. Run: arclio login")

    if not config.is_token_expired():
        return access_token

    # Token expired, attempt refresh
    refresh_token = config.get_refresh_token()
    if not refresh_token:
        raise Exception("Token expired and no refresh token. Run: arclio login")

    client = get_kinde_client()
    tokens = await client.refresh_token(refresh_token)
    config.set_tokens(tokens)

    return tokens.access_token


def get_valid_token_sync() -> str:
    """Synchronous wrapper for get_valid_token."""
    return asyncio.get_event_loop().run_until_complete(get_valid_token())
