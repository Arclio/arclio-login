"""Configuration and credential storage for Arclio Login CLI."""

import json
import os
from pathlib import Path
from typing import Optional

from .types import KindeTokens, StoredCredentials

# Config directory: ~/.config/arclio or ~/.arclio
CONFIG_DIR = Path.home() / ".config" / "arclio"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


def _ensure_config_dir() -> None:
    """Ensure config directory exists with proper permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Set directory permissions to 700 (owner only)
    os.chmod(CONFIG_DIR, 0o700)


def _load_credentials() -> dict:
    """Load credentials from file."""
    if not CREDENTIALS_FILE.exists():
        return {}
    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_credentials(data: dict) -> None:
    """Save credentials to file with secure permissions."""
    _ensure_config_dir()
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    # Set file permissions to 600 (owner read/write only)
    os.chmod(CREDENTIALS_FILE, 0o600)


def get_access_token() -> Optional[str]:
    """Get stored access token."""
    creds = _load_credentials()
    return creds.get("access_token")


def get_refresh_token() -> Optional[str]:
    """Get stored refresh token."""
    creds = _load_credentials()
    return creds.get("refresh_token")


def get_expires_at() -> Optional[int]:
    """Get token expiration timestamp (milliseconds)."""
    creds = _load_credentials()
    return creds.get("expires_at")


def get_user_email() -> Optional[str]:
    """Get stored user email."""
    creds = _load_credentials()
    return creds.get("user_email")


def get_user_id() -> Optional[str]:
    """Get stored user ID."""
    creds = _load_credentials()
    return creds.get("user_id")


def is_token_expired() -> bool:
    """Check if token is expired (with 60-second buffer)."""
    import time

    expires_at = get_expires_at()
    if expires_at is None:
        return True
    # Consider expired 60 seconds before actual expiry
    return time.time() * 1000 > (expires_at - 60000)


def is_authenticated() -> bool:
    """Check if user has stored credentials."""
    return get_access_token() is not None


def set_tokens(tokens: KindeTokens) -> None:
    """Store tokens from OAuth response."""
    import time

    creds = _load_credentials()
    creds["access_token"] = tokens.access_token
    if tokens.refresh_token:
        creds["refresh_token"] = tokens.refresh_token
    if tokens.id_token:
        creds["id_token"] = tokens.id_token
    # Calculate absolute expiry time in milliseconds
    creds["expires_at"] = int(time.time() * 1000) + (tokens.expires_in * 1000)
    _save_credentials(creds)


def set_user_info(email: Optional[str], user_id: str) -> None:
    """Store user info."""
    creds = _load_credentials()
    if email:
        creds["user_email"] = email
    creds["user_id"] = user_id
    _save_credentials(creds)


def clear_credentials() -> None:
    """Clear all stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def get_config_path() -> str:
    """Get path to credentials file."""
    return str(CREDENTIALS_FILE)


def get_stored_credentials() -> Optional[StoredCredentials]:
    """Get all stored credentials as a dataclass."""
    creds = _load_credentials()
    if not creds.get("access_token"):
        return None
    return StoredCredentials(
        access_token=creds["access_token"],
        refresh_token=creds.get("refresh_token"),
        id_token=creds.get("id_token"),
        expires_at=creds.get("expires_at"),
        user_email=creds.get("user_email"),
        user_id=creds.get("user_id"),
    )
