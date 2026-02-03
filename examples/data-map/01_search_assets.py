"""
Example: Search for Data Assets

This example demonstrates how to search for data assets in Purview
using different search criteria.

Prerequisites:
- Service principal with Data Reader role or higher
- .env file configured with credentials

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/discovery/query
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token


def main():
    """Search for data assets using various criteria."""

    # Load credentials from environment
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set in environment")
        print("Copy .env.example to .env and configure your credentials")
        return

    # Get access token
    print("Authenticating...")
    try:
        token = get_access_token()
        print("SUCCESS: Authentication successful\n")
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        return

    # Create client
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)

    # Example 1: Search for all assets (limited results)
    print("=" * 70)
    print("Example 1: Search for All Assets (first 10)")
    print("=" * 70)

    try:
        results = client.search_assets(keywords="*", limit=10)
        print(f"Found {len(results)} assets:\n")

        for i, asset in enumerate(results, 1):
            name = asset.get("name", "N/A")
            type_name = asset.get("typeName", "N/A")
            qualified_name = asset.get("qualifiedName", "N/A")

            print(f"{i}. {name}")
            print(f"   Type: {type_name}")
            print(f"   Qualified Name: {qualified_name[:80]}...")
            print()

    except Exception as e:
        print(f"ERROR: Search failed: {e}\n")

    # Example 2: Search by keyword
    print("=" * 70)
    print("Example 2: Search by Keyword")
    print("=" * 70)

    keyword = input("Enter search keyword (or press Enter for 'sales'): ").strip() or "sales"

    try:
        results = client.search_assets(keywords=keyword, limit=20)
        print(f"\nFound {len(results)} assets matching '{keyword}':\n")

        if not results:
            print("No assets found. Try a different keyword.\n")
        else:
            for i, asset in enumerate(results[:5], 1):  # Show first 5
                name = asset.get("name", "N/A")
                type_name = asset.get("typeName", "N/A")
                print(f"{i}. {name} ({type_name})")

            if len(results) > 5:
                print(f"   ... and {len(results) - 5} more")

        print()

    except Exception as e:
        print(f"ERROR: Search failed: {e}\n")

    # Example 3: Search by entity type
    print("=" * 70)
    print("Example 3: Search by Entity Type")
    print("=" * 70)

    entity_types = [
        "azure_sql_table",
        "databricks_table",
        "adls_gen2_filesystem",
        "azure_blob_container",
    ]

    print("Available entity types:")
    for i, et in enumerate(entity_types, 1):
        print(f"  {i}. {et}")

    choice = input("\nSelect entity type (1-4, or press Enter for 'azure_sql_table'): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(entity_types):
        entity_type = entity_types[int(choice) - 1]
    else:
        entity_type = "azure_sql_table"

    try:
        results = client.search_assets(keywords="*", entity_type=entity_type, limit=10)
        print(f"\nFound {len(results)} assets of type '{entity_type}':\n")

        if not results:
            print(f"No '{entity_type}' assets found in your catalog.\n")
        else:
            for i, asset in enumerate(results, 1):
                name = asset.get("name", "N/A")
                qualified_name = asset.get("qualifiedName", "N/A")
                print(f"{i}. {name}")
                print(f"   Qualified Name: {qualified_name}")
                print()

    except Exception as e:
        print(f"ERROR: Search failed: {e}\n")

    # Example 4: Get entity details
    print("=" * 70)
    print("Example 4: Get Entity Details")
    print("=" * 70)

    if results and len(results) > 0:
        asset = results[0]
        guid = asset.get("id")
        name = asset.get("name")

        print(f"Getting details for: {name}\n")

        try:
            entity = client.get_entity(guid)
            attrs = entity["entity"]["attributes"]

            print(f"Entity GUID: {guid}")
            print(f"Name: {attrs.get('name', 'N/A')}")
            print(f"Type: {entity['entity']['typeName']}")
            print(f"Description: {attrs.get('description', '(no description)')}")
            print(f"Owner: {attrs.get('owner', 'N/A')}")
            print(f"Qualified Name: {attrs.get('qualifiedName', 'N/A')}")

            # Show classifications if present
            classifications = entity["entity"].get("classifications", [])
            if classifications:
                print(f"\nClassifications:")
                for cls in classifications:
                    print(f"  - {cls['typeName']}")

            # Show labels if present
            labels = entity["entity"].get("labels", [])
            if labels:
                print(f"\nLabels: {', '.join(labels)}")

            print()

        except Exception as e:
            print(f"ERROR: Failed to get entity details: {e}\n")

    print("=" * 70)
    print("SUCCESS: Search examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
