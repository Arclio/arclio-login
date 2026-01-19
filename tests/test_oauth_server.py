"""Tests for OAuth callback server."""

import pytest

from arclio_login.oauth_server import OAuthCallbackServer


class TestOAuthCallbackServer:
    """Tests for local OAuth callback server."""

    def test_find_available_port(self):
        """Test finding an available port."""
        server = OAuthCallbackServer()
        port = server._find_available_port([3100, 3101, 3102])

        assert port in [3100, 3101, 3102]

    def test_start_and_close(self):
        """Test starting and stopping server."""
        server = OAuthCallbackServer()

        port = server.start()
        assert port > 0
        assert server.server is not None

        callback_url = server.get_callback_url()
        assert f"http://localhost:{port}/callback" == callback_url

        server.close()
        assert server.server is None

    def test_callback_url_format(self):
        """Test callback URL format."""
        server = OAuthCallbackServer()
        server.port = 3100

        url = server.get_callback_url()

        assert url == "http://localhost:3100/callback"

    @pytest.mark.asyncio
    async def test_wait_for_callback_timeout(self):
        """Test that wait_for_callback times out correctly."""
        server = OAuthCallbackServer()
        server.start()

        try:
            with pytest.raises(Exception, match="timed out"):
                await server.wait_for_callback(timeout=0.1)
        finally:
            server.close()
