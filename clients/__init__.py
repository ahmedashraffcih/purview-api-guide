"""
Microsoft Purview REST API Client Library

Production-ready Python clients for working with Purview REST APIs.

Example usage:
    from clients.datamap_client import PurviewDataMapClient
    from clients.auth import get_access_token
    import os

    # Get credentials from environment
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    token = get_access_token()

    # Create client
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)

    # Search for assets
    results = client.search_assets(keywords="sales")

For detailed examples, see the examples/ directory.

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/
"""

__version__ = "1.0.0"

from clients.auth import get_access_token
from clients.base_client import BaseHTTPClient
from clients.datamap_client import PurviewDataMapClient
from clients.dataquality_client import PurviewDataQualityClient
from clients.workflow_client import PurviewWorkflowClient

__all__ = [
    "get_access_token",
    "BaseHTTPClient",
    "PurviewDataMapClient",
    "PurviewDataQualityClient",
    "PurviewWorkflowClient",
]
