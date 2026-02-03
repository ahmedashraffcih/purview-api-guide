"""
Example: Handling Pagination

This example demonstrates how to handle paginated API responses when
working with large result sets in Purview APIs.

Most Purview list operations support pagination via:
- limit/offset parameters
- continuation tokens (for some endpoints)
- skipToken (for newer APIs)

Prerequisites:
- Service principal with appropriate role for the API surface
- .env file configured with credentials
- Large dataset to paginate through

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.dataquality_client import PurviewDataQualityClient
from clients.auth import get_access_token


def paginate_search_results(client, keywords, entity_type=None, page_size=50, max_pages=10):
    """
    Fetch all search results using pagination.

    Args:
        client: PurviewDataMapClient instance
        keywords: Search keywords
        entity_type: Optional entity type filter
        page_size: Number of results per page
        max_pages: Maximum pages to fetch (safety limit)

    Returns:
        List of all matching assets
    """
    all_results = []
    page = 1

    print(f"Searching for '{keywords}' with pagination...")
    print(f"Page size: {page_size}, Max pages: {max_pages}\n")

    while page <= max_pages:
        print(f"Fetching page {page}...", end=" ")

        # Calculate offset
        offset = (page - 1) * page_size

        # Search with limit
        try:
            results = client.search_assets(
                keywords=keywords,
                entity_type=entity_type,
                limit=page_size
            )

            if not results:
                print("No more results.")
                break

            result_count = len(results)
            all_results.extend(results)

            print(f"Got {result_count} results (Total: {len(all_results)})")

            # If we got fewer results than page_size, we've reached the end
            if result_count < page_size:
                print("Reached end of results.")
                break

            page += 1

        except Exception as e:
            print(f"Error: {e}")
            break

    return all_results


def fetch_all_with_continuation(endpoint_func, initial_params=None, max_iterations=100):
    """
    Generic pagination handler for APIs that use continuation tokens.

    Args:
        endpoint_func: Function that calls the API endpoint
        initial_params: Initial parameters for the first call
        max_iterations: Safety limit on iterations

    Returns:
        List of all results
    """
    all_results = []
    params = initial_params or {}
    iteration = 0

    while iteration < max_iterations:
        try:
            # Call endpoint
            response = endpoint_func(**params)

            # Handle different response structures
            if isinstance(response, dict):
                # Extract results
                results = response.get("value", [])
                all_results.extend(results)

                print(f"Iteration {iteration + 1}: Got {len(results)} items (Total: {len(all_results)})")

                # Check for continuation token
                continuation = response.get("nextLink") or response.get("@nextLink")
                if not continuation:
                    break

                # Update params with continuation token
                # Note: Different APIs use different parameter names
                params["skipToken"] = continuation

            elif isinstance(response, list):
                # Direct list response (no pagination)
                all_results.extend(response)
                break

            else:
                print(f"Unexpected response type: {type(response)}")
                break

            iteration += 1

        except Exception as e:
            print(f"Error during pagination: {e}")
            break

    return all_results


def main():
    """Demonstrate pagination patterns."""

    # Setup
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set")
        return

    print("Authenticating...")
    token = get_access_token()
    datamap_client = PurviewDataMapClient(endpoint=endpoint, access_token=token)
    dq_client = PurviewDataQualityClient(access_token=token)
    print("SUCCESS: Authenticated\n")

    # Example 1: Paginate search results
    print("=" * 70)
    print("Example 1: Paginate Search Results")
    print("=" * 70)
    print()

    try:
        results = paginate_search_results(
            client=datamap_client,
            keywords="*",
            page_size=10,
            max_pages=5
        )

        print(f"\nSUCCESS: Total assets retrieved: {len(results)}")

        if results:
            print("\nSample results:")
            for i, asset in enumerate(results[:5], 1):
                print(f"  {i}. {asset.get('name', 'Unnamed')} ({asset.get('typeName', 'Unknown')})")

    except Exception as e:
        print(f"ERROR: Search failed: {e}")

    # Example 2: Manually handle pagination with offset/limit
    print("\n" + "=" * 70)
    print("Example 2: Manual Offset-Based Pagination")
    print("=" * 70)
    print()

    page_size = 10
    max_results = 30
    all_assets = []

    for offset in range(0, max_results, page_size):
        print(f"Fetching offset {offset}-{offset + page_size}...", end=" ")

        try:
            # Note: Purview search doesn't directly support offset, but this
            # demonstrates the pattern for APIs that do
            results = datamap_client.search_assets(
                keywords="*",
                limit=page_size
            )

            if not results:
                print("No results.")
                break

            all_assets.extend(results)
            print(f"Got {len(results)} results")

            # Break if we got fewer than expected (end of results)
            if len(results) < page_size:
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"\nSUCCESS: Total retrieved: {len(all_assets)}")

    # Example 3: Paginate Data Quality domains
    print("\n" + "=" * 70)
    print("Example 3: List All Business Domains")
    print("=" * 70)
    print()

    try:
        domains = dq_client.list_domains()
        print(f"SUCCESS: Found {len(domains)} business domain(s):")

        for i, domain in enumerate(domains, 1):
            print(f"  {i}. {domain.get('name', 'Unnamed')}")

        # For each domain, get data products (demonstrates nested pagination)
        if domains:
            print("\nFetching data products for each domain...")
            total_products = 0

            for domain in domains[:3]:  # Limit to first 3 domains for demo
                domain_name = domain.get('name', 'Unnamed')
                domain_id = domain['id']

                try:
                    products = dq_client.list_data_products(domain_id)
                    product_count = len(products)
                    total_products += product_count

                    print(f"  {domain_name}: {product_count} product(s)")

                except Exception as e:
                    print(f"  {domain_name}: Error - {e}")

            print(f"\nSUCCESS: Total products across domains: {total_products}")

    except Exception as e:
        print(f"ERROR: Failed to list domains: {e}")

    # Example 4: Batch processing with pagination
    print("\n" + "=" * 70)
    print("Example 4: Batch Processing Pattern")
    print("=" * 70)
    print()

    print("When processing large datasets, use pagination to:")
    print("  1. Reduce memory usage")
    print("  2. Implement progress tracking")
    print("  3. Enable resume on failure")
    print("  4. Avoid API timeouts\n")

    batch_size = 10
    processed = 0
    failed = 0

    try:
        # Fetch in batches
        print(f"Processing assets in batches of {batch_size}...")

        results = datamap_client.search_assets(keywords="*", limit=batch_size)

        for i, asset in enumerate(results, 1):
            try:
                # Simulate processing (e.g., validate, enrich, export)
                asset_name = asset.get('name', 'Unnamed')
                asset_type = asset.get('typeName', 'Unknown')

                # Your processing logic here
                # For example: validate_asset(asset), enrich_metadata(asset), etc.

                processed += 1
                print(f"  [{i}/{len(results)}] SUCCESS: Processed {asset_name}")

            except Exception as e:
                failed += 1
                print(f"  [{i}/{len(results)}] ERROR: Failed: {e}")

        print(f"\nSUCCESS: Batch complete: {processed} processed, {failed} failed")

    except Exception as e:
        print(f"ERROR: Batch processing failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    print("\nPagination Best Practices:")
    print("  • Use reasonable page sizes (10-100 items)")
    print("  • Implement safety limits (max pages/iterations)")
    print("  • Add delays between requests to avoid rate limiting")
    print("  • Handle continuation tokens when available")
    print("  • Log progress for long-running operations")
    print("  • Implement retry logic for transient failures")
    print("  • Consider memory constraints for large datasets")

    print("\nPurview API Pagination Support:")
    print("  • Search API: Uses 'limit' parameter (no built-in offset)")
    print("  • List endpoints: May return full results or support skipToken")
    print("  • Check response for 'nextLink' or '@nextLink' fields")
    print("  • Some endpoints don't support pagination (return all results)")

    print("\n" + "=" * 70)
    print("SUCCESS: Pagination examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
