"""
Example: Create Data Quality Rules

This example demonstrates how to create data quality rules via the REST API.

IMPORTANT: Rules must include a "columns" array in typeProperties to avoid
DQ-MissingColumn errors. See docs/api-limitations.md for details.

Prerequisites:
- Service principal with Data Quality Steward role
- .env file configured with credentials
- Business domain and data product set up in Purview
- Data assets registered in the domain

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/rules/create-or-update-rule
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.dataquality_client import PurviewDataQualityClient
from clients.auth import get_access_token


def main():
    """Create data quality rules."""

    # Setup
    print("Authenticating...")
    token = get_access_token()
    client = PurviewDataQualityClient(access_token=token)
    print("SUCCESS: Authenticated\n")

    # Step 1: List business domains
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

    # Step 2: List data products
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

    # Step 3: Get data asset ID
    print("=" * 70)
    print("Step 3: Enter Data Asset ID")
    print("=" * 70)

    print("You need the Catalog Asset ID (not Data Map GUID).")
    print("Get this from the Purview Portal or use the Data Quality client")
    print("to list assets in the data product.\n")

    asset_id = input("Enter data asset ID: ").strip()

    if not asset_id:
        print("ERROR: Asset ID required")
        return

    # Step 4: Create a quality rule
    print("\n" + "=" * 70)
    print("Step 4: Create Quality Rule")
    print("=" * 70)

    print("\nExample quality rules:")
    print("  1. Check for NULL values in a column")
    print("  2. Check for duplicate values")
    print("  3. Validate value range")
    print()

    rule_type = input("Select rule type (1-3, or press Enter for #1): ").strip() or "1"

    if rule_type == "1":
        column_name = input("Enter column name to check for NULLs: ").strip() or "id"

        rule_id = f"check_nulls_{column_name}"
        rule_body = {
            "name": f"Check Nulls - {column_name}",
            "description": f"Check for NULL values in {column_name} column",
            "type": "CustomSQL",
            "typeProperties": {
                "condition": f"SELECT COUNT(*) FROM {{table}} WHERE {column_name} IS NULL",
                "columns": [
                    {"value": column_name, "type": "Column"}
                ]  # ← REQUIRED to avoid DQ-MissingColumn error
            },
            "severity": "High"
        }

    elif rule_type == "2":
        column_name = input("Enter column name to check for duplicates: ").strip() or "id"

        rule_id = f"check_duplicates_{column_name}"
        rule_body = {
            "name": f"Check Duplicates - {column_name}",
            "description": f"Check for duplicate values in {column_name}",
            "type": "CustomSQL",
            "typeProperties": {
                "condition": f"SELECT {column_name}, COUNT(*) as cnt FROM {{table}} GROUP BY {column_name} HAVING COUNT(*) > 1",
                "columns": [
                    {"value": column_name, "type": "Column"}
                ]
            },
            "severity": "Medium"
        }

    else:
        column_name = input("Enter column name: ").strip() or "age"
        min_val = input("Enter minimum value: ").strip() or "0"
        max_val = input("Enter maximum value: ").strip() or "120"

        rule_id = f"check_range_{column_name}"
        rule_body = {
            "name": f"Check Range - {column_name}",
            "description": f"Check if {column_name} is between {min_val} and {max_val}",
            "type": "CustomSQL",
            "typeProperties": {
                "condition": f"SELECT COUNT(*) FROM {{table}} WHERE {column_name} < {min_val} OR {column_name} > {max_val}",
                "columns": [
                    {"value": column_name, "type": "Column"}
                ]
            },
            "severity": "Medium"
        }

    print(f"\nCreating rule: {rule_body['name']}")
    print(f"Rule ID: {rule_id}")

    try:
        result = client.create_rule(
            business_domain_id=domain_id,
            data_product_id=product_id,
            data_asset_id=asset_id,
            rule_id=rule_id,
            rule_body=rule_body
        )

        print("\nSUCCESS: Rule created successfully!")
        print(f"Rule ID: {result.get('id', rule_id)}")
        print(f"Name: {result.get('name')}")
        print()

    except Exception as e:
        print(f"\nERROR: Failed to create rule: {e}")
        print("\nTroubleshooting:")
        print("  - Verify Data Quality Steward role is assigned")
        print("  - Check that asset ID is correct (use Catalog Asset ID)")
        print("  - Ensure columns array is included in typeProperties")
        print("  - See docs/api-limitations.md for common issues\n")

    print("=" * 70)
    print("SUCCESS: Rule creation example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
