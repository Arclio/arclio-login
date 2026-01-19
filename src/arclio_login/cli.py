"""Arclio Login CLI - Main entry point."""

import asyncio
import sys
import webbrowser

import click
from dotenv import load_dotenv
from rich.console import Console

from . import __version__, config
from .kinde_client import get_kinde_client
from .oauth_server import OAuthCallbackServer
from .token_manager import get_valid_token

# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="arclio")
def main():
    """Arclio CLI for Kinde OAuth authentication.

    Authenticate with Kinde to get tokens for Arclio services.
    """
    pass


@main.command()
def login():
    """Login with Kinde OAuth (opens browser)."""
    client = get_kinde_client()

    if not client.is_configured():
        console.print("[red]Error:[/red] Kinde OAuth not configured")
        console.print()
        console.print("Set environment variables:")
        console.print("  KINDE_AUTH_DOMAIN")
        console.print("  KINDE_CLIENT_ID")
        console.print("  KINDE_CLIENT_SECRET")
        sys.exit(1)

    asyncio.run(_login_async(client))


async def _login_async(client):
    """Async login flow."""
    server = OAuthCallbackServer()

    try:
        server.start()
        callback_url = server.get_callback_url()
        auth_url = client.build_auth_url(callback_url)

        console.print("[blue]Opening browser for authentication...[/blue]")

        try:
            webbrowser.open(auth_url)
        except Exception:
            console.print()
            console.print("Could not open browser automatically.")
            console.print(f"Please open this URL: {auth_url}")

        with console.status("[bold blue]Waiting for authentication...[/bold blue]"):
            result = await server.wait_for_callback()

        if result.error:
            console.print(f"[red]Authentication failed:[/red] {result.error}")
            if result.error_description:
                console.print(f"  {result.error_description}")
            sys.exit(1)

        with console.status("[bold blue]Exchanging code for token...[/bold blue]"):
            tokens = await client.exchange_code_for_token(result.code, callback_url)

        with console.status("[bold blue]Getting user info...[/bold blue]"):
            user = await client.get_user_info(tokens.access_token)

        config.set_tokens(tokens)
        config.set_user_info(user.email, user.sub)

        console.print()
        console.print(f"[green]Authenticated as {user.email or user.sub}[/green]")
        console.print(f"  Credentials saved to: {config.get_config_path()}")

    finally:
        server.close()


@main.command()
@click.option("-q", "--quiet", is_flag=True, help="Output only the token (for scripting)")
def token(quiet: bool):
    """Output current access token (refreshes if expired)."""
    try:
        access_token = asyncio.run(get_valid_token())

        if quiet:
            # Quiet mode: just output the token (no newline for piping)
            click.echo(access_token, nl=False)
        else:
            # Normal mode: show token with context
            email = config.get_user_email()

            console.print()
            console.print("[green]Access Token:[/green]")
            console.print(access_token)
            console.print()
            if email:
                console.print(f"  User: {email}")

    except Exception as e:
        if not quiet:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
def status():
    """Show authentication status."""
    if not config.is_authenticated():
        console.print("[yellow]Status:[/yellow] Not authenticated")
        console.print()
        console.print("Run: [bold]arclio login[/bold]")
        return

    email = config.get_user_email()
    user_id = config.get_user_id()
    expired = config.is_token_expired()

    console.print("[green]Status:[/green] Authenticated")
    if email:
        console.print(f"  User: {email}")
    if user_id:
        console.print(f"  ID: {user_id}")
    token_status = "[yellow]Expired (will refresh)[/yellow]" if expired else "[green]Valid[/green]"
    console.print(f"  Token: {token_status}")
    console.print(f"  Config: {config.get_config_path()}")


@main.command()
def logout():
    """Clear stored credentials."""
    if not config.is_authenticated():
        console.print("Not logged in.")
        return

    config.clear_credentials()
    console.print("[green]Logged out successfully[/green]")


if __name__ == "__main__":
    main()
