# Claude Code Guidelines for arclio-login

This document provides project-specific context for Claude Code when working on arclio-login.

## Project Overview

**Project**: Arclio Login CLI
**Stack**: Python 3.11+, Click, httpx, Rich
**Purpose**: CLI tool for Kinde OAuth authentication, providing easy token management for Arclio services (platform-api, mcp-hub, workflow-prototype).

## Quick Reference

```bash
# Setup
uv sync                    # Install dependencies
uv run poe setup-hooks     # Install pre-commit hooks

# Development
uv run arclio --help       # Run CLI directly
uv run poe pre-commit      # Format, lint, type check
uv run poe test            # Run tests

# Code quality
uv run poe format          # Format code with ruff
uv run poe lint            # Lint with ruff
uv run poe pyright         # Type check
```

## Architecture

```
src/arclio_login/
├── __init__.py          # Package version
├── cli.py               # Click CLI entry point (login, token, status, logout)
├── types.py             # Dataclasses: KindeTokens, KindeUser, StoredCredentials
├── kinde_client.py      # OAuth client: build_auth_url, exchange_code_for_token, refresh_token
├── oauth_server.py      # Local HTTP server for OAuth callback
├── config.py            # Token storage at ~/.config/arclio/credentials.json
└── token_manager.py     # Auto-refresh logic for expired tokens
```

## Key Files

### CLI Commands (`cli.py`)
- `arclio login` - Opens browser for Kinde OAuth, stores tokens
- `arclio token [-q]` - Outputs access token (auto-refreshes if expired)
- `arclio status` - Shows auth status
- `arclio logout` - Clears credentials

### Token Storage (`config.py`)
- Location: `~/.config/arclio/credentials.json`
- Permissions: 600 (owner read/write only)
- Schema: access_token, refresh_token, id_token, expires_at, user_email, user_id

### OAuth Flow (`kinde_client.py`, `oauth_server.py`)
1. Build auth URL with PKCE-like state/nonce
2. Start local server on port 3100-3104
3. Open browser to Kinde auth URL
4. Receive callback with authorization code
5. Exchange code for tokens
6. Store tokens securely

## Environment Variables

```bash
KINDE_AUTH_DOMAIN=https://your-app.kinde.com
KINDE_CLIENT_ID=your_client_id
KINDE_CLIENT_SECRET=your_client_secret
```

## Code Quality Standards

### Linting & Formatting
- **Linter**: Ruff (pycodestyle, pyflakes, isort)
- **Formatter**: Ruff format
- **Type Checker**: Pyright (basic mode)
- **Pre-commit**: Run `poe pre-commit` before pushing

### Type Hints
- Required on all function signatures
- Use `from typing import Optional` as needed
- Async functions should use proper async types

### Line Length
- 100 characters (ruff default)

## Testing

```bash
uv run poe test           # Run all tests
uv run poe test-cov       # Run with coverage
```

Tests are in `tests/` directory using pytest with pytest-asyncio.

## Common Tasks

### Adding a New Command
1. Add command function in `cli.py`
2. Decorate with `@main.command()`
3. Add tests in `tests/test_cli.py`

### Modifying Token Storage
1. Update schema in `config.py`
2. Update `StoredCredentials` dataclass in `types.py`
3. Ensure backwards compatibility

### Updating OAuth Flow
1. Modify `kinde_client.py` for auth logic
2. Modify `oauth_server.py` for callback handling
3. Test with real Kinde credentials

## Integration with Other Arclio Services

This CLI is used by:
- **workflow-prototype**: `KINDE_TOKEN=$(arclio token -q)`
- **platform-api**: curl with Bearer token
- **mcp-hub**: curl with Bearer token

Example:
```bash
curl -H "Authorization: Bearer $(arclio token -q)" https://api.arclio.com/workflows
```

## Security Considerations

- Credentials stored with 600 permissions (owner only)
- Config directory created with 700 permissions
- Client secret should never be logged
- Tokens auto-expire and refresh automatically

## PR Checklist

- [ ] Passes `poe pre-commit` (format, lint, pyright)
- [ ] Tests added/updated
- [ ] Type hints on all functions
- [ ] No secrets committed
- [ ] CLAUDE.md updated if architecture changes
