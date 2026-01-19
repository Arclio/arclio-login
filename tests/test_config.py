"""Tests for config module."""

import json
import os
from pathlib import Path

from arclio_login import config
from arclio_login.types import KindeTokens


class TestConfigStorage:
    """Tests for credential storage."""

    def test_set_and_get_tokens(self, temp_config_dir: Path):
        """Test storing and retrieving tokens."""
        tokens = KindeTokens(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            id_token="test_id_token",
            expires_in=3600,
        )

        config.set_tokens(tokens)

        assert config.get_access_token() == "test_access_token"
        assert config.get_refresh_token() == "test_refresh_token"

    def test_set_user_info(self, temp_config_dir: Path):
        """Test storing user info."""
        config.set_user_info("test@example.com", "user_123")

        assert config.get_user_email() == "test@example.com"
        assert config.get_user_id() == "user_123"

    def test_clear_credentials(self, temp_config_dir: Path):
        """Test clearing credentials."""
        tokens = KindeTokens(access_token="test_token", expires_in=3600)
        config.set_tokens(tokens)
        config.set_user_info("test@example.com", "user_123")

        config.clear_credentials()

        assert config.get_access_token() is None
        assert config.get_user_email() is None

    def test_is_authenticated(self, temp_config_dir: Path):
        """Test authentication check."""
        assert not config.is_authenticated()

        tokens = KindeTokens(access_token="test_token", expires_in=3600)
        config.set_tokens(tokens)

        assert config.is_authenticated()

    def test_token_expiry(self, temp_config_dir: Path):
        """Test token expiry detection."""
        # Token that expires in 1 hour - not expired
        tokens = KindeTokens(access_token="test_token", expires_in=3600)
        config.set_tokens(tokens)

        assert not config.is_token_expired()

    def test_token_expired(self, temp_config_dir: Path):
        """Test expired token detection."""
        # Manually set an expired timestamp
        creds = {"access_token": "test", "expires_at": 1000}  # Way in the past
        creds_file = temp_config_dir / "credentials.json"
        with open(creds_file, "w") as f:
            json.dump(creds, f)

        assert config.is_token_expired()

    def test_file_permissions(self, temp_config_dir: Path):
        """Test that credentials file has secure permissions."""
        tokens = KindeTokens(access_token="test_token", expires_in=3600)
        config.set_tokens(tokens)

        creds_file = temp_config_dir / "credentials.json"
        mode = os.stat(creds_file).st_mode & 0o777

        assert mode == 0o600, f"Expected 600, got {oct(mode)}"


class TestStoredCredentials:
    """Tests for StoredCredentials dataclass."""

    def test_get_stored_credentials(self, temp_config_dir: Path):
        """Test getting all credentials as dataclass."""
        tokens = KindeTokens(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_in=3600,
        )
        config.set_tokens(tokens)
        config.set_user_info("test@example.com", "user_123")

        creds = config.get_stored_credentials()

        assert creds is not None
        assert creds.access_token == "test_access"
        assert creds.refresh_token == "test_refresh"
        assert creds.user_email == "test@example.com"
        assert creds.user_id == "user_123"

    def test_get_stored_credentials_empty(self, temp_config_dir: Path):
        """Test getting credentials when not authenticated."""
        creds = config.get_stored_credentials()
        assert creds is None
