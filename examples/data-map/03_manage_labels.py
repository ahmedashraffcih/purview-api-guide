"""
Example: Manage Labels

This example demonstrates how to add and remove free-text labels on assets.
Labels are useful for organizing and filtering assets without formal classifications.

Prerequisites:
- Service principal with Data Curator role or higher
- .env file configured with credentials

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/add-labels
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token


def main():
    """Demonstrate label management."""

    # Setup
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set")
        return

    print("Authenticating...")
    token = get_access_token()
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)
    print("SUCCESS: Authenticated\n")

    # Find an asset
    print("=" * 70)
    print("Finding an Asset to Label")
    print("=" * 70)

    results = client.search_assets(keywords="*", limit=5)
    if not results:
        print("ERROR: No assets found in catalog")
        return

    print(f"Found {len(results)} assets:\n")
    for i, asset in enumerate(results, 1):
        print(f"{i}. {asset.get('name')} ({asset.get('typeName')})")

    choice = input("\nSelect asset (1-5, or press Enter for #1): ").strip() or "1"
    selected_asset = results[int(choice) - 1 if choice.isdigit() else 0]

    guid = selected_asset["id"]
    name = selected_asset["name"]

    print(f"\nSUCCESS: Selected: {name}")
    print(f"   GUID: {guid}\n")

    # View existing labels
    print("=" * 70)
    print("Current Labels")
    print("=" * 70)

    entity = client.get_entity(guid)
    existing_labels = entity["entity"].get("labels", [])

    if existing_labels:
        print(f"Labels on '{name}':")
        for label in existing_labels:
            print(f"  - {label}")
    else:
        print(f"No labels on '{name}' yet.")

    print()

    # Add labels
    print("=" * 70)
    print("Add Labels")
    print("=" * 70)

    print("Label suggestions:")
    print("  - Production, Development, Test")
    print("  - Critical, Important, Standard")
    print("  - Daily, Weekly, Monthly")
    print("  - CustomerData, FinancialData, OperationalData")
    print()

    label_input = input("Enter labels to add (comma-separated): ").strip()

    if label_input:
        new_labels = [l.strip() for l in label_input.split(",")]

        # Combine with existing labels (avoid duplicates)
        all_labels = list(set(existing_labels + new_labels))

        try:
            client.add_labels(guid, all_labels)
            print(f"SUCCESS: Labels added successfully!\n")

            # Verify
            entity = client.get_entity(guid)
            updated_labels = entity["entity"].get("labels", [])

            print(f"Updated labels on '{name}':")
            for label in updated_labels:
                print(f"  - {label}")
            print()

        except Exception as e:
            print(f"ERROR: Failed to add labels: {e}\n")

    print("=" * 70)
    print("SUCCESS: Label management complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
