"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from arclio_login import config
from arclio_login.cli import main
from arclio_login.types import KindeTokens


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestStatusCommand:
    """Tests for status command."""

    def test_status_not_authenticated(self, runner: CliRunner, temp_config_dir: Path):
        """Test status when not authenticated."""
        result = runner.invoke(main, ["status"])

        assert result.exit_code == 0
        assert "Not authenticated" in result.output

    def test_status_authenticated(self, runner: CliRunner, temp_config_dir: Path):
        """Test status when authenticated."""
        tokens = KindeTokens(access_token="test_token", expires_in=3600)
        config.set_tokens(tokens)
        config.set_user_info("test@example.com", "user_123")

        result = runner.invoke(main, ["status"])

        assert result.exit_code == 0
        assert "Authenticated" in result.output
        assert "test@example.com" in result.output


class TestLogoutCommand:
    """Tests for logout command."""

    def test_logout_when_not_logged_in(self, runner: CliRunner, temp_config_dir: Path):
        """Test logout when not authenticated."""
        result = runner.invoke(main, ["logout"])

        assert result.exit_code == 0
        assert "Not logged in" in result.output

    def test_logout_when_logged_in(self, runner: CliRunner, temp_config_dir: Path):
        """Test logout when authenticated."""
        tokens = KindeTokens(access_token="test_token", expires_in=3600)
        config.set_tokens(tokens)

        result = runner.invoke(main, ["logout"])

        assert result.exit_code == 0
        assert "Logged out" in result.output
        assert not config.is_authenticated()


class TestTokenCommand:
    """Tests for token command."""

    def test_token_not_authenticated(self, runner: CliRunner, temp_config_dir: Path):
        """Test token when not authenticated."""
        result = runner.invoke(main, ["token"])

        assert result.exit_code == 1

    def test_token_quiet_mode(self, runner: CliRunner, temp_config_dir: Path):
        """Test token in quiet mode."""
        tokens = KindeTokens(access_token="test_access_token", expires_in=3600)
        config.set_tokens(tokens)

        result = runner.invoke(main, ["token", "-q"])

        assert result.exit_code == 0
        assert result.output == "test_access_token"  # No newline in quiet mode


class TestLoginCommand:
    """Tests for login command."""

    def test_login_not_configured(self, runner: CliRunner, temp_config_dir: Path):
        """Test login when Kinde not configured."""
        with patch.dict("os.environ", {}, clear=True):
            # Need to reset the singleton to pick up new env vars
            import arclio_login.kinde_client as kc

            kc._kinde_client = None

            result = runner.invoke(main, ["login"])

            assert result.exit_code == 1
            assert "not configured" in result.output


class TestVersion:
    """Tests for version flag."""

    def test_version(self, runner: CliRunner):
        """Test --version flag."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output
