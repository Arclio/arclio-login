"""Type definitions for Arclio Login CLI."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class KindeTokens:
    """Tokens received from Kinde OAuth."""

    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600


@dataclass
class KindeUser:
    """User info from Kinde."""

    sub: str
    email: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


@dataclass
class StoredCredentials:
    """Credentials stored locally."""

    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    expires_at: Optional[int] = None  # Unix timestamp in milliseconds
    user_email: Optional[str] = None
    user_id: Optional[str] = None
