"""Local OAuth callback server for receiving OAuth redirects."""

import asyncio
import html
import socket
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Optional
from urllib.parse import parse_qs, urlparse

from .logo import LOGO_DATA_URI

DEFAULT_PORTS = [3100, 3101, 3102, 3103, 3104]
CALLBACK_TIMEOUT = 120  # seconds


@dataclass
class OAuthCallbackResult:
    """Result from OAuth callback."""

    code: str
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class OAuthCallbackServer:
    """Local HTTP server to receive OAuth callback."""

    def __init__(self):
        self.port: int = 0
        self.server: Optional[HTTPServer] = None
        self.result: Optional[OAuthCallbackResult] = None
        self._server_thread: Optional[Thread] = None

    def _find_available_port(self, ports: list[int] = DEFAULT_PORTS) -> int:
        """Find first available port from list."""
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue
        raise Exception(f"No available ports in range: {ports}")

    def start(self, ports: list[int] = DEFAULT_PORTS) -> int:
        """Start server on available port."""
        self.port = self._find_available_port(ports)
        server_instance = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                # Suppress logging
                pass

            def do_GET(self):
                parsed = urlparse(self.path)

                if parsed.path == "/callback":
                    params = parse_qs(parsed.query)

                    error = params.get("error", [None])[0]
                    if error:
                        server_instance.result = OAuthCallbackResult(
                            code="",
                            error=error,
                            error_description=params.get("error_description", [None])[0],
                        )
                        self._send_error_page(error, params.get("error_description", [""])[0])
                        return

                    code = params.get("code", [None])[0]
                    if not code:
                        server_instance.result = OAuthCallbackResult(
                            code="",
                            error="missing_code",
                            error_description="Authorization code not received",
                        )
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"Authorization code missing")
                        return

                    # Success
                    server_instance.result = OAuthCallbackResult(
                        code=code,
                        state=params.get("state", [None])[0],
                    )
                    self._send_success_page()

                elif parsed.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"status": "ok"}')

                else:
                    self.send_response(404)
                    self.end_headers()

            def _send_success_page(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    f"""<!DOCTYPE html>
<html>
<head>
    <title>Authentication Successful</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #fff;
        }}
        .container {{
            text-align: center;
            max-width: 400px;
            padding: 2rem;
        }}
        .logo {{
            width: 160px;
            margin-bottom: 2rem;
        }}
        .status-icon {{
            font-size: 64px;
            color: #22c55e;
            margin-bottom: 1rem;
        }}
        h1 {{
            color: #000;
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }}
        p {{
            color: #666;
            margin: 0.25rem 0;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="{LOGO_DATA_URI}" alt="Arclio" class="logo">
        <div class="status-icon">&#10003;</div>
        <h1>Authentication Successful</h1>
        <p>You can close this window and return to the terminal.</p>
    </div>
    <script>setTimeout(() => window.close(), 3000)</script>
</body>
</html>""".encode()
                )

            def _send_error_page(self, error: str, description: str):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                safe_error = html.escape(str(error))
                safe_desc = html.escape(str(description or "Unknown error"))
                self.wfile.write(
                    f"""<!DOCTYPE html>
<html>
<head>
    <title>Authentication Failed</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #fff;
        }}
        .container {{
            text-align: center;
            max-width: 400px;
            padding: 2rem;
        }}
        .logo {{
            width: 160px;
            margin-bottom: 2rem;
        }}
        .status-icon {{
            font-size: 64px;
            color: #ef4444;
            margin-bottom: 1rem;
        }}
        h1 {{
            color: #000;
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }}
        p {{
            color: #666;
            margin: 0.25rem 0;
            font-size: 0.9rem;
        }}
        .error {{
            color: #ef4444;
            font-family: monospace;
            font-size: 0.8rem;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="{LOGO_DATA_URI}" alt="Arclio" class="logo">
        <div class="status-icon">&#10007;</div>
        <h1>Authentication Failed</h1>
        <p>There was an error during authentication.</p>
        <p class="error">{safe_error}: {safe_desc}</p>
        <p>You can close this window and return to the terminal.</p>
    </div>
    <script>setTimeout(() => window.close(), 3000)</script>
</body>
</html>""".encode()
                )

        self.server = HTTPServer(("127.0.0.1", self.port), CallbackHandler)
        self._server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self._server_thread.start()

        return self.port

    def get_callback_url(self) -> str:
        """Get callback URL for OAuth redirect."""
        return f"http://localhost:{self.port}/callback"

    async def wait_for_callback(self, timeout: float = CALLBACK_TIMEOUT) -> OAuthCallbackResult:
        """Wait for OAuth callback with timeout."""
        start_time = asyncio.get_event_loop().time()

        while True:
            if self.result:
                return self.result

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                self.close()
                raise Exception("Authentication timed out. Please try again.")

            await asyncio.sleep(0.1)

    def close(self) -> None:
        """Shutdown server."""
        if self.server:
            self.server.shutdown()
            self.server = None
