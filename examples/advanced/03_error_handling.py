"""
Example: Robust Error Handling

This example demonstrates best practices for handling errors when working
with Purview REST APIs, including:
- Authentication failures
- Authorization (RBAC) errors
- API-specific errors
- Rate limiting
- Transient failures
- Data validation errors

Prerequisites:
- Service principal with appropriate roles
- .env file configured with credentials

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/
"""

import os
import sys
import time
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.dataquality_client import PurviewDataQualityClient
from clients.auth import get_access_token
import requests


class PurviewAPIError(Exception):
    """Base exception for Purview API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 error_code: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


def safe_authenticate(max_retries=3, retry_delay=5):
    """
    Authenticate with retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Seconds to wait between retries

    Returns:
        Access token string

    Raises:
        PurviewAPIError: If authentication fails after retries
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Authentication attempt {attempt}/{max_retries}...")
            token = get_access_token()
            print("SUCCESS: Authentication successful")
            return token

        except requests.HTTPError as e:
            if attempt == max_retries:
                raise PurviewAPIError(
                    message="Authentication failed after retries",
                    status_code=getattr(e.response, 'status_code', None),
                    error_code="AUTH_FAILED"
                )

            print(f"WARNING: Authentication failed, retrying in {retry_delay}s...")
            time.sleep(retry_delay)

        except Exception as e:
            raise PurviewAPIError(
                message=f"Unexpected authentication error: {e}",
                error_code="AUTH_ERROR"
            )


def safe_api_call(func, *args, max_retries=3, **kwargs):
    """
    Execute API call with comprehensive error handling.

    Args:
        func: API function to call
        *args: Positional arguments for the function
        max_retries: Maximum retry attempts for retryable errors
        **kwargs: Keyword arguments for the function

    Returns:
        API response

    Raises:
        PurviewAPIError: On non-retryable errors or after max retries
    """
    retryable_codes = [429, 500, 502, 503, 504]
    attempt = 0

    while attempt < max_retries:
        try:
            return func(*args, **kwargs)

        except requests.HTTPError as e:
            status_code = e.response.status_code
            attempt += 1

            # Try to parse error response
            try:
                error_body = e.response.json()
                error_code = error_body.get("code", "UNKNOWN")
                error_msg = error_body.get("message", str(e))
            except:
                error_code = f"HTTP_{status_code}"
                error_msg = str(e)

            # Handle specific error types
            if status_code == 401:
                raise PurviewAPIError(
                    message="Authentication failed. Token may be expired.",
                    status_code=401,
                    error_code="UNAUTHORIZED"
                )

            elif status_code == 403:
                raise PurviewAPIError(
                    message="Permission denied. Check RBAC role assignments.",
                    status_code=403,
                    error_code="FORBIDDEN",
                    details={"hint": "Verify service principal has required Purview roles"}
                )

            elif status_code == 404:
                raise PurviewAPIError(
                    message=f"Resource not found: {error_msg}",
                    status_code=404,
                    error_code="NOT_FOUND"
                )

            elif status_code == 400:
                raise PurviewAPIError(
                    message=f"Bad request: {error_msg}",
                    status_code=400,
                    error_code=error_code,
                    details={"hint": "Check request parameters and payload format"}
                )

            elif status_code in retryable_codes:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"WARNING: HTTP {status_code} (attempt {attempt}/{max_retries}). "
                          f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise PurviewAPIError(
                        message=f"API call failed after {max_retries} retries: {error_msg}",
                        status_code=status_code,
                        error_code=error_code
                    )

            else:
                raise PurviewAPIError(
                    message=f"API error: {error_msg}",
                    status_code=status_code,
                    error_code=error_code
                )

        except PurviewAPIError:
            raise

        except Exception as e:
            raise PurviewAPIError(
                message=f"Unexpected error: {e}",
                error_code="UNEXPECTED_ERROR"
            )


def validate_guid(guid: str) -> bool:
    """
    Validate GUID format.

    Args:
        guid: GUID string to validate

    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, guid.lower()))


def main():
    """Demonstrate error handling patterns."""

    print("=" * 70)
    print("Error Handling Examples")
    print("=" * 70)
    print()

    # Example 1: Handle authentication errors
    print("Example 1: Authentication Error Handling")
    print("-" * 70)

    try:
        token = safe_authenticate(max_retries=3)
        print(f"Token acquired (length: {len(token)})\n")

    except PurviewAPIError as e:
        print(f"ERROR: Authentication failed: {e.message}")
        print(f"   Error code: {e.error_code}")
        if e.details:
            print(f"   Details: {e.details}")
        return

    # Setup clients
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set")
        return

    datamap_client = PurviewDataMapClient(endpoint=endpoint, access_token=token)

    # Example 2: Handle 404 errors (resource not found)
    print("\nExample 2: Handle Resource Not Found")
    print("-" * 70)

    fake_guid = "00000000-0000-0000-0000-000000000000"

    # Validate GUID format first
    if not validate_guid(fake_guid):
        print(f"ERROR: Invalid GUID format: {fake_guid}")
    else:
        try:
            entity = safe_api_call(datamap_client.get_entity, fake_guid)
            print(f"SUCCESS: Entity found: {entity}")

        except PurviewAPIError as e:
            if e.status_code == 404:
                print(f"WARNING: Entity not found: {fake_guid}")
                print("   This is expected for non-existent GUIDs")
            else:
                print(f"ERROR: Error: {e.message}")

    # Example 3: Handle search errors
    print("\nExample 3: Handle Search Errors")
    print("-" * 70)

    try:
        # Search with valid parameters
        results = safe_api_call(
            datamap_client.search_assets,
            keywords="test",
            limit=5
        )
        print(f"SUCCESS: Search successful: Found {len(results)} results")

    except PurviewAPIError as e:
        print(f"ERROR: Search failed: {e.message}")
        print(f"   Status code: {e.status_code}")
        print(f"   Error code: {e.error_code}")

        if e.status_code == 400:
            print("   Hint: Check search parameters format")
        elif e.status_code == 403:
            print("   Hint: Service principal needs Data Reader role")

    # Example 4: Handle RBAC errors
    print("\nExample 4: Detect RBAC Issues")
    print("-" * 70)

    print("Testing for RBAC permissions...")

    operations = [
        ("Search assets", lambda: datamap_client.search_assets(keywords="*", limit=1)),
        ("List glossaries", lambda: datamap_client.get("/catalog/api/atlas/v2/glossary",
                                                        params={"api-version": "2023-09-01"}))
    ]

    for op_name, op_func in operations:
        try:
            safe_api_call(op_func)
            print(f"  SUCCESS: {op_name}: OK")

        except PurviewAPIError as e:
            if e.status_code == 403:
                print(f"  ERROR: {op_name}: Permission denied")
                print(f"     Required role may be missing")
            else:
                print(f"  WARNING: {op_name}: {e.error_code}")

    # Example 5: Validate input before API calls
    print("\nExample 5: Input Validation")
    print("-" * 70)

    test_guids = [
        "12345",  # Invalid format
        "not-a-guid",  # Invalid format
        "00000000-0000-0000-0000-000000000000",  # Valid format but doesn't exist
    ]

    for guid in test_guids:
        if validate_guid(guid):
            print(f"  SUCCESS: Valid GUID format: {guid}")
        else:
            print(f"  ERROR: Invalid GUID format: {guid}")
            print(f"     Skipping API call to avoid 400 error")

    # Example 6: Batch operation error handling
    print("\nExample 6: Batch Operation Error Handling")
    print("-" * 70)

    print("Processing multiple operations with error tracking...")

    operations_log = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "errors": []
    }

    # Simulate batch processing
    asset_guids = ["guid-1", "guid-2", "guid-3"]  # Would be real GUIDs

    for guid in asset_guids:
        operations_log["total"] += 1

        try:
            if not validate_guid(guid):
                raise ValueError(f"Invalid GUID format: {guid}")

            # Would do actual operation here
            # result = safe_api_call(datamap_client.get_entity, guid)

            operations_log["success"] += 1
            print(f"  SUCCESS: Processed {guid}")

        except (PurviewAPIError, ValueError) as e:
            operations_log["failed"] += 1
            operations_log["errors"].append({
                "guid": guid,
                "error": str(e)
            })
            print(f"  ERROR: Failed {guid}: {e}")

    print(f"\nBatch Summary:")
    print(f"  Total: {operations_log['total']}")
    print(f"  Success: {operations_log['success']}")
    print(f"  Failed: {operations_log['failed']}")

    # Summary
    print("\n" + "=" * 70)
    print("Error Handling Best Practices")
    print("=" * 70)

    print("""
    1. Authentication:
       - Implement retry logic for transient failures
       - Cache tokens and refresh before expiration
       - Handle 401 errors with token refresh

    2. Authorization (RBAC):
       - Detect 403 errors early
       - Provide clear messages about required roles
       - Document role requirements in code

    3. Input Validation:
       - Validate GUIDs, emails, and other inputs before API calls
       - Check for required fields
       - Verify data types and formats

    4. Rate Limiting:
       - Implement exponential backoff for 429 errors
       - Add delays between batch operations
       - Monitor Retry-After headers

    5. Transient Errors:
       - Retry 5xx errors with backoff
       - Set maximum retry limits
       - Log retry attempts for debugging

    6. Batch Operations:
       - Track success/failure counts
       - Log errors with context
       - Continue processing on individual failures
       - Implement checkpointing for large batches

    7. Error Reporting:
       - Include error codes in exceptions
       - Provide actionable error messages
       - Link to troubleshooting documentation
       - Log errors with full context

    8. API-Specific Errors:
       - Handle known API limitations (see docs/api-limitations.md)
       - Implement workarounds for documented issues
       - Provide fallback strategies
    """)

    print("=" * 70)
    print("SUCCESS: Error handling examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
