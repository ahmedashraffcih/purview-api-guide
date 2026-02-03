"""
Authentication helper for Microsoft Purview REST APIs.

Provides service principal (client credentials) authentication with automatic
token caching and refresh.

Official documentation:
https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow
"""

import os
import time
from typing import Optional
import requests


# Global token cache
_cached_token: Optional[str] = None
_token_expires_at: float = 0


def get_access_token(force_refresh: bool = False) -> str:
    """
    Acquire OAuth2 access token for Purview APIs using service principal credentials.

    Tokens are cached and automatically refreshed 2 minutes before expiration.

    Args:
        force_refresh: Force token refresh even if cached token is valid

    Returns:
        Bearer token string (valid for ~60 minutes)

    Raises:
        ValueError: If required environment variables are missing
        requests.HTTPError: If token acquisition fails

    Environment Variables:
        TENANT_ID: Azure AD tenant ID (required)
        CLIENT_ID: Service principal client ID (required)
        CLIENT_SECRET: Service principal client secret (required)

    Example:
        >>> import os
        >>> os.environ['TENANT_ID'] = 'your-tenant-id'
        >>> os.environ['CLIENT_ID'] = 'your-client-id'
        >>> os.environ['CLIENT_SECRET'] = 'your-client-secret'
        >>> token = get_access_token()
        >>> print(f"Token length: {len(token)}")

    Official documentation:
    https://learn.microsoft.com/en-us/azure/purview/tutorial-using-rest-apis
    """
    global _cached_token, _token_expires_at

    # Check if we need to refresh (2-minute buffer before expiration)
    now = time.time()
    if not force_refresh and _cached_token and now < (_token_expires_at - 120):
        return _cached_token

    # Load credentials from environment
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    # Validate required credentials
    missing = []
    if not tenant_id:
        missing.append("TENANT_ID")
    if not client_id:
        missing.append("CLIENT_ID")
    if not client_secret:
        missing.append("CLIENT_SECRET")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please set them in your .env file or environment."
        )

    # Request token from Azure AD
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://purview.azure.net/.default",
    }

    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        token_data = response.json()

        _cached_token = token_data["access_token"]
        expires_in = int(token_data.get("expires_in", 3600))
        _token_expires_at = now + expires_in

        return _cached_token

    except requests.HTTPError as e:
        raise requests.HTTPError(
            f"Failed to acquire access token: {e}. "
            f"Verify your service principal credentials and RBAC roles."
        ) from e
    except KeyError as e:
        raise ValueError(
            f"Invalid token response - missing field: {e}"
        ) from e


def load_env_from_file(env_path: str = ".env") -> None:
    """
    Load environment variables from .env file.

    Supports basic .env format:
    - KEY=value
    - KEY="value with spaces"
    - # comments
    - Inline comments (KEY=value # comment)

    Args:
        env_path: Path to .env file (default: ".env")

    Note:
        If python-dotenv is installed, it will be used automatically.
        Otherwise, a simple built-in parser is used.
    """
    # Try using python-dotenv if available
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
        return
    except ImportError:
        pass

    # Fallback to simple parser
    if not os.path.exists(env_path):
        return

    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#") or "=" not in line:
                continue

            # Parse KEY=value
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Handle inline comments
            if "#" in value:
                value = value.split("#", 1)[0].strip()

            # Remove surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Only set if not already in environment
            if key and value and key not in os.environ:
                os.environ[key] = value


# Auto-load .env on import
load_env_from_file()
