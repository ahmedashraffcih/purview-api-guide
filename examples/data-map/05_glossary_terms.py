"""
Example: Manage Glossary Terms

This example demonstrates how to create and manage glossary terms via the API.

Prerequisites:
- Service principal with Data Curator role or higher
- .env file configured with credentials
- At least one glossary created in Purview Portal

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/glossary
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token


def main():
    """Demonstrate glossary term management."""

    # Setup
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set")
        return

    print("Authenticating...")
    token = get_access_token()
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)
    print("SUCCESS: Authenticated\n")

    # List glossaries
    print("=" * 70)
    print("Step 1: Select a Glossary")
    print("=" * 70)

    try:
        glossaries = client.list_glossaries()

        if not glossaries:
            print("ERROR: No glossaries found.")
            print("Create a glossary in the Purview Portal first:")
            print("  Data Map → Glossaries → New Glossary")
            return

        print(f"Found {len(glossaries)} glossaries:\n")
        for i, glossary in enumerate(glossaries, 1):
            print(f"{i}. {glossary['name']}")

        choice = input("\nSelect glossary (or press Enter for #1): ").strip() or "1"
        glossary = glossaries[int(choice) - 1 if choice.isdigit() else 0]

        glossary_guid = glossary["guid"]
        glossary_name = glossary["name"]

        print(f"\nSUCCESS: Selected glossary: {glossary_name}")
        print(f"   GUID: {glossary_guid}\n")

    except Exception as e:
        print(f"ERROR: Failed to list glossaries: {e}")
        return

    # Create glossary term
    print("=" * 70)
    print("Step 2: Create Glossary Term")
    print("=" * 70)

    print("Example business terms:")
    print("  - Customer Lifetime Value")
    print("  - Churn Rate")
    print("  - Annual Recurring Revenue")
    print("  - Net Promoter Score")
    print()

    term_name = input("Enter term name: ").strip()

    if not term_name:
        print("Term name required")
        return

    term_description = input("Enter term description: ").strip()

    print(f"\nCreating term '{term_name}' in glossary '{glossary_name}'...")

    try:
        term = client.create_glossary_term(
            name=term_name,
            glossary_guid=glossary_guid,
            description=term_description or None
        )

        print("\nSUCCESS: Glossary term created successfully!")
        print(f"Term GUID: {term['guid']}")
        print(f"Name: {term['name']}")
        if term_description:
            print(f"Description: {term_description}")
        print()

    except Exception as e:
        print(f"\nERROR: Failed to create glossary term: {e}")
        print("\nTroubleshooting:")
        print("  - Verify Data Curator role is assigned")
        print("  - Check that term name doesn't already exist")
        print("  - Ensure glossary GUID is correct\n")

    print("=" * 70)
    print("SUCCESS: Glossary term example complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  - Link terms to assets in Purview Portal")
    print("  - Create term hierarchies (parent/child relationships)")
    print("  - Add synonyms and related terms")


if __name__ == "__main__":
    main()
