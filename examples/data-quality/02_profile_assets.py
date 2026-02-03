"""
Example: Profile Data Assets

This example demonstrates how to trigger data profiling jobs via the REST API
and monitor their status.

IMPORTANT: The REST API can trigger and monitor profiling jobs but CANNOT
retrieve profiling statistics. View profiling results in the Purview Portal UI.
See docs/api-limitations.md for details.

Prerequisites:
- Service principal with Data Quality Steward role
- .env file configured with credentials
- Business domain and data product set up in Purview
- Data assets registered with data source connection configured
- Data source connection ID (get from Purview Portal)

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/profiling
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.dataquality_client import PurviewDataQualityClient
from clients.auth import get_access_token


def main():
    """Trigger and monitor asset profiling."""

    # Setup
    print("Authenticating...")
    token = get_access_token()
    client = PurviewDataQualityClient(access_token=token)
    print("SUCCESS: Authenticated\n")

    # Step 1: Select business domain
    print("=" * 70)
    print("Step 1: Select Business Domain")
    print("=" * 70)

    try:
        domains = client.list_domains()

        if not domains:
            print("ERROR: No business domains found.")
            print("Create a business domain in the Purview Portal first.")
            return

        print(f"Found {len(domains)} business domains:\n")
        for i, domain in enumerate(domains, 1):
            print(f"{i}. {domain['name']}")

        choice = input("\nSelect domain (or press Enter for #1): ").strip() or "1"
        domain = domains[int(choice) - 1 if choice.isdigit() else 0]

        domain_id = domain["id"]
        print(f"\nSUCCESS: Selected domain: {domain['name']}")
        print(f"   ID: {domain_id}\n")

    except Exception as e:
        print(f"ERROR: Failed to list domains: {e}")
        return

    # Step 2: Select data product
    print("=" * 70)
    print("Step 2: Select Data Product")
    print("=" * 70)

    try:
        products = client.list_data_products(domain_id)

        if not products:
            print("ERROR: No data products found in this domain.")
            return

        print(f"Found {len(products)} data products:\n")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['name']}")

        choice = input("\nSelect product (or press Enter for #1): ").strip() or "1"
        product = products[int(choice) - 1 if choice.isdigit() else 0]

        product_id = product["id"]
        print(f"\nSUCCESS: Selected product: {product['name']}")
        print(f"   ID: {product_id}\n")

    except Exception as e:
        print(f"ERROR: Failed to list products: {e}")
        return

    # Step 3: Enter data asset and connection details
    print("=" * 70)
    print("Step 3: Configure Profiling")
    print("=" * 70)

    print("\nYou need:")
    print("  1. Data Asset ID (Catalog Asset ID)")
    print("  2. Data Source Connection ID")
    print("  3. Data source type (e.g., AzureSqlDatabase, Delta)")
    print("\nGet these from the Purview Portal:\n")
    print("  Asset ID: Unified Catalog → Data Products → [Product] → Data Assets")
    print("  Connection ID: Data Map → Data Sources → [Source] → Properties\n")

    asset_id = input("Enter data asset ID: ").strip()
    if not asset_id:
        print("ERROR: Asset ID required")
        return

    connection_id = input("Enter data source connection ID: ").strip()
    if not connection_id:
        print("ERROR: Connection ID required")
        return

    print("\nCommon data source types:")
    print("  1. AzureSqlDatabase")
    print("  2. Delta (Databricks)")
    print("  3. AzureDataLakeStorageGen2")
    print("  4. AzureSynapseAnalytics")

    ds_type_choice = input("\nSelect type (or press Enter for #1): ").strip() or "1"
    ds_types = ["AzureSqlDatabase", "Delta", "AzureDataLakeStorageGen2", "AzureSynapseAnalytics"]
    ds_type = ds_types[int(ds_type_choice) - 1 if ds_type_choice.isdigit() and int(ds_type_choice) <= 4 else 0]

    # Step 4: Configure profile scope
    print("\n" + "=" * 70)
    print("Step 4: Configure Profile Scope")
    print("=" * 70)

    if ds_type in ["AzureSqlDatabase", "AzureSynapseAnalytics"]:
        print("\nFor SQL sources, specify tables to profile:")
        schema = input("Enter schema name (or press Enter for 'dbo'): ").strip() or "dbo"
        table = input("Enter table name: ").strip()

        if not table:
            print("ERROR: Table name required for SQL sources")
            return

        profile_config = {
            "type": ds_type,
            "dataSourceId": connection_id,
            "tables": [
                {
                    "schema": schema,
                    "table": table
                }
            ]
        }

    elif ds_type == "Delta":
        print("\nFor Delta sources, specify catalog/schema/table:")
        catalog = input("Enter catalog name: ").strip()
        schema = input("Enter schema name: ").strip()
        table = input("Enter table name: ").strip()

        if not all([catalog, schema, table]):
            print("ERROR: Catalog, schema, and table required for Delta sources")
            return

        profile_config = {
            "type": ds_type,
            "dataSourceId": connection_id,
            "tables": [
                {
                    "catalog": catalog,
                    "schema": schema,
                    "table": table
                }
            ]
        }

    else:
        # Generic config for other sources
        profile_config = {
            "type": ds_type,
            "dataSourceId": connection_id
        }

    # Step 5: Trigger profiling
    print("\n" + "=" * 70)
    print("Step 5: Trigger Profiling Job")
    print("=" * 70)

    print(f"\nProfile configuration:")
    print(f"  Type: {ds_type}")
    print(f"  Connection: {connection_id}")
    print(f"  Asset: {asset_id}\n")

    confirm = input("Start profiling job? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    try:
        run_id = client.profile_asset(
            business_domain_id=domain_id,
            data_product_id=product_id,
            data_asset_id=asset_id,
            profile_config=profile_config
        )

        print(f"\nSUCCESS: Profiling job triggered!")
        print(f"Run ID: {run_id}\n")

    except Exception as e:
        print(f"\nERROR: Failed to trigger profiling: {e}")
        print("\nCommon issues:")
        print("  - Data source connection not configured correctly")
        print("  - Profile config 'type' doesn't match data source type")
        print("  - Asset not properly registered in the data product")
        print("  - Missing Data Quality Steward role")
        print("\nSee docs/api-limitations.md for troubleshooting.\n")
        return

    # Step 6: Monitor job status
    print("=" * 70)
    print("Step 6: Monitor Job Status")
    print("=" * 70)

    monitor = input("\nMonitor job status? (y/n): ").strip().lower()
    if monitor != 'y':
        print(f"\nYou can check status later with run ID: {run_id}")
        print("Or view results in Purview Portal:")
        print("  Unified Catalog → Data Products → [Product] → Data Assets → [Asset] → Quality → Profile\n")
        return

    print("\nMonitoring job (polling every 10 seconds, max 5 minutes)...\n")

    max_attempts = 30  # 5 minutes
    attempt = 0

    while attempt < max_attempts:
        try:
            status = client.get_run_status(
                business_domain_id=domain_id,
                run_id=run_id
            )

            job_status = status.get("status", "Unknown")
            start_time = status.get("submissionTime", "")
            end_time = status.get("endTime", "")

            print(f"[{attempt + 1}/{max_attempts}] Status: {job_status}", end="")
            if end_time:
                print(f" (completed at {end_time})")
            else:
                print()

            if job_status == "Succeeded":
                print("\nSUCCESS: Profiling completed successfully!")
                print("\nView profiling statistics in Purview Portal:")
                print("  Unified Catalog → Data Products → [Product]")
                print("  → Data Assets → [Asset] → Quality → Profile tab")
                print("\nNote: Profiling statistics are NOT available via REST API.")
                break

            elif job_status == "Failed":
                error_msg = status.get("message", "Unknown error")
                print(f"\nERROR: Profiling failed: {error_msg}")
                print("\nCommon errors:")
                print("  - DQ-DSL-BuildError: Profile config doesn't match data source")
                print("  - Connection errors: Verify data source connectivity")
                print("  - Permission errors: Check service principal RBAC roles")
                break

            elif job_status == "Skipped":
                print("\nWARNING: Profiling skipped (data unchanged since last run)")
                print("Previous profiling results are still valid.")
                break

            elif job_status in ["Queued", "InProgress"]:
                time.sleep(10)
                attempt += 1

            else:
                print(f"\nWARNING: Unexpected status: {job_status}")
                break

        except Exception as e:
            print(f"\nERROR: Failed to get status: {e}")
            break

    if attempt >= max_attempts:
        print("\nINFO: Job still running after 5 minutes.")
        print(f"Check status later with run ID: {run_id}")

    print("\n" + "=" * 70)
    print("SUCCESS: Profiling example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
