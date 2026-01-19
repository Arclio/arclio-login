"""Tests for Kinde OAuth client."""

import os
from unittest.mock import patch

from arclio_login.kinde_client import KindeClient, get_kinde_client


class TestKindeClient:
    """Tests for KindeClient."""

    def test_is_configured_with_env_vars(self, mock_env_vars):
        """Test client configuration detection with env vars."""
        client = KindeClient()
        assert client.is_configured()

    def test_is_configured_without_env_vars(self):
        """Test client configuration detection without env vars."""
        with patch.dict(os.environ, {}, clear=True):
            client = KindeClient()
            assert not client.is_configured()

    def test_build_auth_url(self, mock_env_vars):
        """Test OAuth authorization URL building."""
        client = KindeClient()
        redirect_uri = "http://localhost:3100/callback"

        url = client.build_auth_url(redirect_uri)

        assert "https://test.kinde.com/oauth2/auth" in url
        assert "client_id=test_client_id" in url
        assert f"redirect_uri={redirect_uri}" in url
        assert "response_type=code" in url
        assert "scope=openid" in url and "profile" in url and "email" in url and "offline" in url
        assert "state=" in url
        assert "nonce=" in url

    def test_build_auth_url_with_custom_config(self):
        """Test URL building with custom configuration."""
        client = KindeClient(
            domain="https://custom.kinde.com",
            client_id="custom_id",
            client_secret="custom_secret",
        )

        url = client.build_auth_url("http://localhost:3100/callback")

        assert "https://custom.kinde.com/oauth2/auth" in url
        assert "client_id=custom_id" in url

    def test_decode_token(self, mock_env_vars):
        """Test JWT token decoding."""
        client = KindeClient()

        # Create a simple JWT-like token (base64 encoded)
        import base64
        import json

        header = (
            base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode()).decode().rstrip("=")
        )
        payload = (
            base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "sub": "user_123",
                        "email": "test@example.com",
                        "given_name": "Test",
                        "family_name": "User",
                    }
                ).encode()
            )
            .decode()
            .rstrip("=")
        )
        signature = base64.urlsafe_b64encode(b"fake_signature").decode().rstrip("=")

        token = f"{header}.{payload}.{signature}"

        user = client._decode_token(token)

        assert user.sub == "user_123"
        assert user.email == "test@example.com"
        assert user.given_name == "Test"
        assert user.family_name == "User"


class TestKindeClientSingleton:
    """Tests for singleton behavior."""

    def test_get_kinde_client_returns_same_instance(self, mock_env_vars):
        """Test that get_kinde_client returns singleton."""
        # Reset singleton
        import arclio_login.kinde_client as kc

        kc._kinde_client = None

        client1 = get_kinde_client()
        client2 = get_kinde_client()

        assert client1 is client2
