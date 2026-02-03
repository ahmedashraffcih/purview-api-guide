"""
Example: Monitor Data Quality

This example demonstrates how to monitor data quality by:
- Listing quality rules for an asset
- Viewing rule details
- Checking run history
- Monitoring quality assessment status

Prerequisites:
- Service principal with Data Quality Steward role
- .env file configured with credentials
- Business domain, data product, and data assets set up
- Quality rules already created

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/rules
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.dataquality_client import PurviewDataQualityClient
from clients.auth import get_access_token


def format_timestamp(ts_str):
    """Format ISO timestamp to readable string."""
    if not ts_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts_str


def main():
    """Monitor data quality rules and assessments."""

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

    # Step 3: Select data asset
    print("=" * 70)
    print("Step 3: Select Data Asset")
    print("=" * 70)

    try:
        assets = client.list_data_assets(domain_id, product_id)

        if not assets:
            print("ERROR: No data assets found in this product.")
            return

        print(f"Found {len(assets)} data assets:\n")
        for i, asset in enumerate(assets, 1):
            name = asset.get("name", "Unnamed")
            asset_type = asset.get("assetType", "Unknown")
            print(f"{i}. {name} ({asset_type})")

        choice = input("\nSelect asset (or press Enter for #1): ").strip() or "1"
        asset = assets[int(choice) - 1 if choice.isdigit() else 0]

        asset_id = asset["id"]
        asset_name = asset.get("name", "Unnamed")
        print(f"\nSUCCESS: Selected asset: {asset_name}")
        print(f"   ID: {asset_id}\n")

    except Exception as e:
        print(f"ERROR: Failed to list assets: {e}")
        return

    # Step 4: List quality rules
    print("=" * 70)
    print("Step 4: Quality Rules Summary")
    print("=" * 70)

    try:
        rules = client.list_rules(
            business_domain_id=domain_id,
            data_product_id=product_id,
            data_asset_id=asset_id
        )

        if not rules:
            print("ERROR: No quality rules found for this asset.")
            print("\nCreate rules using: examples/data-quality/01_create_rules.py")
            return

        print(f"\nFound {len(rules)} quality rules:\n")

        for i, rule in enumerate(rules, 1):
            rule_name = rule.get("name", "Unnamed")
            rule_type = rule.get("type", "Unknown")
            severity = rule.get("severity", "Unknown")
            rule_id = rule.get("id", "N/A")

            print(f"{i}. {rule_name}")
            print(f"   Type: {rule_type} | Severity: {severity}")
            print(f"   ID: {rule_id}")
            print()

    except Exception as e:
        print(f"ERROR: Failed to list rules: {e}")
        return

    # Step 5: View rule details
    print("=" * 70)
    print("Step 5: Rule Details")
    print("=" * 70)

    choice = input(f"\nView details for which rule? (1-{len(rules)}, or press Enter to skip): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(rules):
        selected_rule = rules[int(choice) - 1]
        rule_id = selected_rule["id"]

        try:
            rule_details = client.get_rule(
                business_domain_id=domain_id,
                data_product_id=product_id,
                data_asset_id=asset_id,
                rule_id=rule_id
            )

            print(f"\nRule: {rule_details.get('name')}")
            print(f"ID: {rule_id}")
            print(f"Type: {rule_details.get('type')}")
            print(f"Severity: {rule_details.get('severity')}")
            print(f"Description: {rule_details.get('description', 'N/A')}")

            type_props = rule_details.get("typeProperties", {})
            if "condition" in type_props:
                print(f"\nSQL Condition:")
                print(f"  {type_props['condition']}")

            if "columns" in type_props:
                columns = [col.get("value") for col in type_props["columns"]]
                print(f"\nColumns: {', '.join(columns)}")

            print()

        except Exception as e:
            print(f"ERROR: Failed to get rule details: {e}\n")

    # Step 6: Check run history
    print("=" * 70)
    print("Step 6: Quality Assessment Run History")
    print("=" * 70)

    try:
        runs = client.list_runs(
            data_asset_id=asset_id,
            run_type="Quality"  # "Quality" for rule scans, "Profile" for profiling
        )

        if not runs:
            print("\nWARNING: No quality assessment runs found.")
            print("\nRules must be executed (manually or via schedule) to see run history.")
            print("Trigger scans in the Purview Portal:")
            print("  Unified Catalog → Data Products → [Product]")
            print("  → Data Assets → [Asset] → Quality → Run Now\n")
        else:
            print(f"\nFound {len(runs)} quality assessment runs:\n")

            # Sort runs by submission time (newest first)
            sorted_runs = sorted(
                runs,
                key=lambda r: r.get("submissionTime", ""),
                reverse=True
            )

            for i, run in enumerate(sorted_runs[:10], 1):  # Show last 10 runs
                run_id = run.get("runId", "N/A")
                status = run.get("status", "Unknown")
                submitted = format_timestamp(run.get("submissionTime"))
                ended = format_timestamp(run.get("endTime"))
                job_type = run.get("jobType", "Unknown")

                print(f"{i}. Run {run_id}")
                print(f"   Status: {status}")
                print(f"   Job Type: {job_type}")
                print(f"   Started: {submitted}")
                print(f"   Ended: {ended}")

                if status == "Failed":
                    error_msg = run.get("message", "No error details")
                    print(f"   Error: {error_msg}")

                print()

            if len(runs) > 10:
                print(f"   ... and {len(runs) - 10} more runs")

    except Exception as e:
        print(f"ERROR: Failed to get run history: {e}\n")

    # Step 7: Monitor specific run
    print("=" * 70)
    print("Step 7: Check Specific Run Status")
    print("=" * 70)

    run_id = input("\nEnter run ID to check (or press Enter to skip): ").strip()

    if run_id:
        try:
            status = client.get_run_status(
                business_domain_id=domain_id,
                run_id=run_id
            )

            print(f"\nRun ID: {run_id}")
            print(f"Status: {status.get('status')}")
            print(f"Job Type: {status.get('jobType', 'N/A')}")
            print(f"Started: {format_timestamp(status.get('submissionTime'))}")
            print(f"Ended: {format_timestamp(status.get('endTime'))}")

            if status.get("status") == "Failed":
                print(f"Error: {status.get('message', 'Unknown error')}")

            if status.get("status") == "Succeeded":
                print("\nSUCCESS: Quality assessment completed successfully!")
                print("\nView detailed results in Purview Portal:")
                print("  Unified Catalog → Data Products → [Product]")
                print("  → Data Assets → [Asset] → Quality tab")

            print()

        except Exception as e:
            print(f"ERROR: Failed to get run status: {e}\n")

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    print(f"\nAsset: {asset_name}")
    print(f"Quality Rules: {len(rules)}")
    print(f"Assessment Runs: {len(runs) if 'runs' in locals() else 0}")

    print("\nNext Steps:")
    print("  - View quality scores in Purview Portal UI")
    print("  - Set up scheduled quality scans")
    print("  - Configure alerts for quality failures")
    print("  - Create additional rules as needed")

    print("\n" + "=" * 70)
    print("SUCCESS: Quality monitoring example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
