"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "arclio"
        config_dir.mkdir()
        with patch("arclio_login.config.CONFIG_DIR", config_dir):
            with patch("arclio_login.config.CREDENTIALS_FILE", config_dir / "credentials.json"):
                yield config_dir


@pytest.fixture
def mock_env_vars():
    """Mock Kinde environment variables."""
    env = {
        "KINDE_AUTH_DOMAIN": "https://test.kinde.com",
        "KINDE_CLIENT_ID": "test_client_id",
        "KINDE_CLIENT_SECRET": "test_client_secret",
    }
    with patch.dict(os.environ, env):
        yield env
