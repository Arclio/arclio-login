# arclio-login

Arclio CLI for Kinde OAuth authentication. Get tokens easily for use with platform-api, mcp-hub, and workflow-prototype.

## Installation

```bash
# Install directly from GitHub
uv pip install git+https://github.com/Arclio/arclio-login.git

# Or with pip
pip install git+https://github.com/Arclio/arclio-login.git
```

## Configuration

Set the following environment variables (or create a `.env` file):

```bash
KINDE_AUTH_DOMAIN=https://your-app.kinde.com
KINDE_CLIENT_ID=your_client_id
KINDE_CLIENT_SECRET=your_client_secret
```

## Usage

### Login

Opens browser for Kinde OAuth authentication:

```bash
arclio login
```

### Get Token

Output your access token (auto-refreshes if expired):

```bash
# With user info
arclio token

# Quiet mode for scripting
arclio token -q
```

### Use with curl

```bash
curl -H "Authorization: Bearer $(arclio token -q)" https://api.arclio.com/workflows
```

### Use with workflow-prototype

```bash
# Add to .env
echo "KINDE_TOKEN=$(arclio token -q)" >> .env
```

### Check Status

```bash
arclio status
```

### Logout

```bash
arclio logout
```

## Token Storage

Credentials are stored securely at:
- `~/.config/arclio/credentials.json` (Linux/macOS)

The file has permissions set to `600` (owner read/write only).

## Development

```bash
# Clone the repo
git clone https://github.com/Arclio/arclio-login.git
cd arclio-login

# Install in development mode
uv pip install -e .

# Run directly
uv run arclio --help
```

## License

Copyright 2025 Arclio. All rights reserved.
