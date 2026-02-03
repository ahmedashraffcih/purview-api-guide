"""
Example: Bulk Operations

This example demonstrates how to perform bulk operations efficiently,
such as updating descriptions for multiple assets.

Prerequisites:
- Service principal with Data Curator role or higher
- .env file configured with credentials
- Multiple assets in your catalog

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token


def bulk_add_labels(client, asset_guids, labels):
    """
    Add labels to multiple assets.

    Args:
        client: PurviewDataMapClient instance
        asset_guids: List of asset GUIDs
        labels: List of label strings to add

    Returns:
        Dictionary with success/failure counts
    """
    results = {"success": 0, "failed": 0, "errors": []}

    for i, guid in enumerate(asset_guids, 1):
        try:
            # Get existing labels
            entity = client.get_entity(guid)
            existing_labels = entity["entity"].get("labels", [])

            # Merge with new labels (deduplicate)
            all_labels = list(set(existing_labels + labels))

            # Update
            client.add_labels(guid, all_labels)
            results["success"] += 1

            print(f"  [{i}/{len(asset_guids)}] SUCCESS: {guid[:8]}...")

            # Rate limiting: small delay between requests
            time.sleep(0.5)

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"guid": guid, "error": str(e)})
            print(f"  [{i}/{len(asset_guids)}] ERROR: {guid[:8]}... - {e}")

    return results


def bulk_update_descriptions(client, updates):
    """
    Update descriptions for multiple assets.

    Args:
        client: PurviewDataMapClient instance
        updates: List of dicts with keys: guid, description

    Returns:
        Dictionary with success/failure counts
    """
    results = {"success": 0, "failed": 0, "errors": []}

    for i, update in enumerate(updates, 1):
        guid = update["guid"]
        description = update["description"]

        try:
            client.set_description(guid, description)
            results["success"] += 1
            print(f"  [{i}/{len(updates)}] SUCCESS: Updated {guid[:8]}...")

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"guid": guid, "error": str(e)})
            print(f"  [{i}/{len(updates)}] ERROR: Failed {guid[:8]}... - {e}")

    return results


def main():
    """Demonstrate bulk operations."""

    # Setup
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set")
        return

    print("Authenticating...")
    token = get_access_token()
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)
    print("SUCCESS: Authenticated\n")

    # Get sample assets
    print("=" * 70)
    print("Finding Assets for Bulk Operations")
    print("=" * 70)

    results = client.search_assets(keywords="*", limit=20)

    if len(results) < 2:
        print("ERROR: Need at least 2 assets for bulk operations demo")
        return

    print(f"Found {len(results)} assets. Selecting first 5 for demo:\n")

    selected_assets = results[:5]
    for i, asset in enumerate(selected_assets, 1):
        print(f"{i}. {asset.get('name')} - {asset['id'][:8]}...")

    print()

    # Example 1: Bulk add labels
    print("=" * 70)
    print("Example 1: Bulk Add Labels")
    print("=" * 70)

    asset_guids = [asset["id"] for asset in selected_assets]
    labels_to_add = ["BulkProcessed", "APIManaged"]

    print(f"Adding labels {labels_to_add} to {len(asset_guids)} assets...\n")

    results = bulk_add_labels(client, asset_guids, labels_to_add)

    print(f"\nSUCCESS: Bulk label operation complete!")
    print(f"   Success: {results['success']}")
    print(f"   Failed: {results['failed']}")

    if results['errors']:
        print("\nErrors:")
        for error in results['errors'][:3]:  # Show first 3
            print(f"  - {error['guid'][:8]}...: {error['error']}")

    print()

    # Example 2: Bulk update descriptions
    print("=" * 70)
    print("Example 2: Bulk Update Descriptions")
    print("=" * 70)

    updates = [
        {
            "guid": asset["id"],
            "description": f"Asset {asset.get('name')} - Updated via API bulk operation"
        }
        for asset in selected_assets[:3]  # Update first 3 only
    ]

    print(f"Updating descriptions for {len(updates)} assets...\n")

    results = bulk_update_descriptions(client, updates)

    print(f"\nSUCCESS: Bulk description update complete!")
    print(f"   Success: {results['success']}")
    print(f"   Failed: {results['failed']}")
    print()

    # Best practices
    print("=" * 70)
    print("Best Practices for Bulk Operations")
    print("=" * 70)

    print("""
1. **Rate Limiting**: Add delays between requests (0.5-1 second)
   - Prevents 429 errors
   - Clients handle retries, but prevention is better

2. **Error Handling**: Track successes and failures separately
   - Don't fail entire batch on one error
   - Log errors for later retry

3. **Progress Tracking**: Show progress for long operations
   - Print status every N items
   - Estimate completion time

4. **Batching**: Process in chunks for very large operations
   - 50-100 items per batch
   - Allows checkpointing and resume

5. **Idempotency**: Design operations to be safely retried
   - Check existing state before updating
   - Use deduplicate logic (like label merging above)

Example batching pattern:

def process_in_batches(items, batch_size=50):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        process_batch(batch)
        time.sleep(2)  # Pause between batches
    """)

    print("=" * 70)
    print("SUCCESS: Bulk operations example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
