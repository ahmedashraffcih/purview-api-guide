"""
Example: Set Business Metadata

This example demonstrates how to set custom business metadata attributes on assets.

IMPORTANT: Business metadata types must be pre-created in Purview Portal and
configured as applicable to the target entity type. See docs/api-limitations.md.

Prerequisites:
- Service principal with Data Curator role or higher
- .env file configured with credentials
- Business metadata type created in Purview Portal

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/add-or-update-business-metadata
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token


def main():
    """Demonstrate business metadata management."""

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
    print("Step 1: Select an Asset")
    print("=" * 70)

    results = client.search_assets(keywords="*", limit=5)
    if not results:
        print("ERROR: No assets found")
        return

    print(f"Found {len(results)} assets:\n")
    for i, asset in enumerate(results, 1):
        print(f"{i}. {asset.get('name')} ({asset.get('typeName')})")

    choice = input("\nSelect asset (1-5, or press Enter for #1): ").strip() or "1"
    selected_asset = results[int(choice) - 1 if choice.isdigit() else 0]

    guid = selected_asset["id"]
    name = selected_asset["name"]
    entity_type = selected_asset["typeName"]

    print(f"\nSUCCESS: Selected: {name}")
    print(f"   Type: {entity_type}")
    print(f"   GUID: {guid}\n")

    # Set business metadata
    print("=" * 70)
    print("Step 2: Set Business Metadata")
    print("=" * 70)

    print("Business metadata types must be created in Purview Portal first:")
    print("  Data Map → Business Metadata → Create New Type\n")

    print("Example business metadata types:")
    print("  - DataQuality (attributes: completeness, accuracy, last_validated)")
    print("  - BusinessContext (attributes: owner, department, cost_center)")
    print("  - Compliance (attributes: retention_period, classification_level)")
    print()

    bm_type = input("Enter business metadata type name: ").strip()

    if not bm_type:
        print("Skipping business metadata example")
        return

    print(f"\nEnter attribute values for '{bm_type}':")
    print("(Press Enter with empty value to finish)\n")

    attributes = {}
    while True:
        attr_name = input("  Attribute name: ").strip()
        if not attr_name:
            break

        attr_value = input(f"  Value for '{attr_name}': ").strip()
        if attr_value:
            attributes[attr_name] = attr_value

    if not attributes:
        print("No attributes specified")
        return

    print(f"\nSetting business metadata '{bm_type}' on '{name}':")
    for key, value in attributes.items():
        print(f"  {key}: {value}")

    try:
        client.set_business_metadata(
            guid=guid,
            business_metadata_name=bm_type,
            attributes=attributes
        )

        print("\nSUCCESS: Business metadata set successfully!\n")

        # Verify
        entity = client.get_entity(guid)
        bm_data = entity["entity"].get("businessAttributes", {})

        if bm_type in bm_data:
            print(f"Verified business metadata '{bm_type}':")
            for key, value in bm_data[bm_type].items():
                print(f"  {key}: {value}")
        print()

    except Exception as e:
        error_msg = str(e)
        print(f"\nERROR: Failed to set business metadata: {error_msg}\n")

        if "ATLAS-404-00-007" in error_msg or "not applicable" in error_msg.lower():
            print("WARNING: Business metadata type not applicable to this entity type.")
            print("\nTo fix:")
            print(f"  1. Go to Purview Portal → Data Map → Business Metadata")
            print(f"  2. Edit the '{bm_type}' type")
            print(f"  3. Add '{entity_type}' to 'Applicable Entity Types'")
            print(f"     OR set 'Applicable Entity Types' to 'DataSet' (universal)")
            print("\nSee docs/api-limitations.md for more details.\n")
        else:
            print("Troubleshooting:")
            print(f"  - Verify business metadata type '{bm_type}' exists")
            print("  - Check that type is applicable to entity type")
            print("  - Ensure attribute names match type definition")
            print("  - Verify Data Curator role is assigned\n")

    print("=" * 70)
    print("SUCCESS: Business metadata example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
