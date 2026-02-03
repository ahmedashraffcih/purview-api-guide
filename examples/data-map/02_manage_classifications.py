"""
Example: Manage Classifications

This example demonstrates how to add, view, and manage classifications
(like PII, Confidential, Sensitive) on Purview assets.

Prerequisites:
- Service principal with Data Curator role or higher
- .env file configured with credentials
- At least one asset in your catalog

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/add-classification
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token


def main():
    """Demonstrate classification management."""

    # Setup
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set")
        return

    print("Authenticating...")
    token = get_access_token()
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)
    print("SUCCESS: Authenticated\n")

    # Step 1: Find an asset to work with
    print("=" * 70)
    print("Step 1: Find an Asset")
    print("=" * 70)

    print("Searching for assets...")
    results = client.search_assets(keywords="*", limit=10)

    if not results:
        print("ERROR: No assets found in catalog. Please register some assets first.")
        return

    print(f"Found {len(results)} assets. Select one:\n")

    for i, asset in enumerate(results[:5], 1):
        print(f"{i}. {asset.get('name')} ({asset.get('typeName')})")

    choice = input("\nSelect asset (1-5, or press Enter for #1): ").strip() or "1"
    selected_asset = results[int(choice) - 1 if choice.isdigit() else 0]

    guid = selected_asset["id"]
    name = selected_asset["name"]

    print(f"\nSUCCESS: Selected: {name}")
    print(f"   GUID: {guid}\n")

    # Step 2: View existing classifications
    print("=" * 70)
    print("Step 2: View Existing Classifications")
    print("=" * 70)

    try:
        entity = client.get_entity(guid)
        existing_classifications = entity["entity"].get("classifications", [])

        if existing_classifications:
            print(f"Current classifications on '{name}':")
            for cls in existing_classifications:
                print(f"  - {cls['typeName']}")
        else:
            print(f"No classifications on '{name}' yet.")

        print()

    except Exception as e:
        print(f"ERROR: Failed to get classifications: {e}\n")
        return

    # Step 3: Add new classifications
    print("=" * 70)
    print("Step 3: Add Classifications")
    print("=" * 70)

    print("Common classifications:")
    print("  1. MICROSOFT.PERSONAL.NAME")
    print("  2. MICROSOFT.PERSONAL.EMAIL")
    print("  3. MICROSOFT.FINANCIAL.CREDIT_CARD")
    print("  4. MICROSOFT.PERSONAL.SSN")

    print("\nNote: These are built-in classifications.")
    print("You can also create custom classifications in the Purview Portal.\n")

    classification_input = input(
        "Enter classification names (comma-separated, or press Enter to skip): "
    ).strip()

    if classification_input:
        new_classifications = [c.strip() for c in classification_input.split(",")]

        # Deduplicate - only add classifications that don't already exist
        existing_names = {cls["typeName"] for cls in existing_classifications}
        to_add = [c for c in new_classifications if c not in existing_names]

        if not to_add:
            print("All specified classifications already exist on this entity.\n")
        else:
            print(f"\nAdding classifications: {', '.join(to_add)}")

            try:
                client.add_classifications(guid, to_add)
                print("SUCCESS: Classifications added successfully!\n")

                # Verify
                entity = client.get_entity(guid)
                updated_classifications = entity["entity"].get("classifications", [])

                print(f"Updated classifications on '{name}':")
                for cls in updated_classifications:
                    print(f"  - {cls['typeName']}")

                print()

            except Exception as e:
                print(f"ERROR: Failed to add classifications: {e}")
                print("\nPossible issues:")
                print("  - Classification type doesn't exist")
                print("  - Insufficient permissions (need Data Curator role)")
                print("  - Classification already associated\n")

    # Step 4: Best practice - check before adding
    print("=" * 70)
    print("Step 4: Safe Classification Add (with duplicate check)")
    print("=" * 70)

    print("Demonstrating safe add pattern that avoids duplicate errors:\n")

    print("""
def add_classification_safe(client, guid, classification_names):
    '''Add classifications only if not already present.'''
    # Get existing classifications
    entity = client.get_entity(guid)
    existing = {c["typeName"] for c in entity["entity"].get("classifications", [])}

    # Filter out duplicates
    to_add = [c for c in classification_names if c not in existing]

    if to_add:
        client.add_classifications(guid, to_add)
        print(f"Added: {', '.join(to_add)}")
    else:
        print("All classifications already present")
    """)

    print("\nThis pattern prevents 'classification already associated' errors.")
    print("See docs/api-limitations.md for more details.\n")

    print("=" * 70)
    print("SUCCESS: Classification management examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
