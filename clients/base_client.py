"""
Base HTTP client with retry logic for Microsoft Purview REST APIs.

Provides:
- Automatic retry for rate limiting (429) and transient errors (5xx)
- Exponential backoff
- Bearer token authentication
- Request/response logging
- Error handling

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/
"""

import time
from typing import Any, Dict, Optional
import requests


class BaseHTTPClient:
    """
    Base HTTP client for Purview REST APIs with retry logic.

    Features:
    - Exponential backoff retry for 429 (rate limit) and 5xx errors
    - Automatic bearer token authentication
    - Configurable timeout and retry attempts
    - Clean error messages

    Example:
        >>> client = BaseHTTPClient(
        ...     base_url="https://your-account.purview.azure.com",
        ...     access_token="your-bearer-token"
        ... )
        >>> response = client.get("/datamap/api/atlas/v2/types/typedefs",
        ...                       params={"api-version": "2023-09-01"})

    Official documentation:
    https://learn.microsoft.com/en-us/rest/api/purview/
    """

    def __init__(
        self,
        base_url: str,
        access_token: str,
        max_retries: int = 5,
        timeout: int = 120
    ):
        """
        Initialize base HTTP client.

        Args:
            base_url: Base URL for API requests (e.g., https://account.purview.azure.com)
            access_token: OAuth2 bearer token
            max_retries: Maximum number of retry attempts for transient errors
            timeout: Request timeout in seconds

        Raises:
            ValueError: If base_url or access_token is empty
        """
        if not base_url:
            raise ValueError("base_url is required")
        if not access_token:
            raise ValueError("access_token is required")

        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers with bearer token."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        Execute HTTP request with exponential backoff retry logic.

        Automatically retries on:
        - 429 (Too Many Requests) - rate limiting
        - 500, 502, 503, 504 - transient server errors

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: URL path (relative or absolute)
            params: Query parameters
            json: Request body (will be JSON-serialized)
            headers: Additional headers

        Returns:
            Response object

        Raises:
            requests.HTTPError: On non-retryable errors or after max retries
        """
        # Build full URL
        if path.startswith("http"):
            url = path
        elif path.startswith("/"):
            url = self.base_url + path
        else:
            url = f"{self.base_url}/{path}"

        headers = self._headers(headers)
        backoff = 2.0

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                    timeout=self.timeout,
                )

                # Check for retryable status codes
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        # Get retry delay from Retry-After header if available
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            wait_time = int(retry_after)
                        else:
                            wait_time = backoff

                        print(
                            f"HTTP {response.status_code} on attempt {attempt + 1}/{self.max_retries + 1}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                        backoff *= 1.7  # Exponential backoff
                        continue

                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    print(
                        f"Request exception on attempt {attempt + 1}/{self.max_retries + 1}: {e}. "
                        f"Retrying in {backoff:.1f}s..."
                    )
                    time.sleep(backoff)
                    backoff *= 1.7
                    continue
                break

        # All retries exhausted
        if last_exception:
            raise requests.HTTPError(
                f"Request failed after {self.max_retries + 1} attempts: {last_exception}"
            ) from last_exception
        else:
            # HTTP error after retries
            raise requests.HTTPError(
                f"HTTP {response.status_code} after {self.max_retries + 1} attempts: {response.text[:200]}"
            )

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Execute GET request.

        Args:
            path: URL path
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object

        Example:
            >>> response = client.get("/datamap/api/atlas/v2/types/typedefs",
            ...                       params={"api-version": "2023-09-01"})
            >>> data = response.json()
        """
        return self._request_with_retry("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Execute POST request.

        Args:
            path: URL path
            json: Request body (will be JSON-serialized)
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object

        Example:
            >>> response = client.post("/datamap/api/search/query",
            ...                        json={"keywords": "sales"},
            ...                        params={"api-version": "2023-09-01"})
            >>> data = response.json()
        """
        return self._request_with_retry("POST", path, params=params, json=json, headers=headers)

    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Execute PUT request.

        Args:
            path: URL path
            json: Request body (will be JSON-serialized)
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object
        """
        return self._request_with_retry("PUT", path, params=params, json=json, headers=headers)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Execute DELETE request.

        Args:
            path: URL path
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object
        """
        return self._request_with_retry("DELETE", path, params=params, headers=headers)
