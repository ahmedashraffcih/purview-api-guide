"""
Example: Create Approval Workflow

This example demonstrates how to create an approval workflow in Purview.
Workflows can be triggered by various governance actions like glossary term
creation, data access requests, or custom integrations.

Prerequisites:
- Service principal with Workflow Admin role
- .env file configured with credentials
- Purview account with workflows feature enabled

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflows/create-or-replace
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.workflow_client import PurviewWorkflowClient
from clients.auth import get_access_token


def create_glossary_approval_workflow():
    """
    Create a workflow that requires approval for new glossary term creation.

    Returns:
        Dictionary with workflow configuration
    """
    return {
        "name": "Glossary Term Approval",
        "description": "Require approval before creating new glossary terms",
        "triggers": [
            {
                "type": "when_term_creation_is_requested",
                "underGlossaryHierarchy": "/glossaries/Glossary"  # Adjust to your glossary path
            }
        ],
        "isEnabled": True,
        "actionDag": {
            "actions": {
                "Start": {
                    "type": "Start",
                    "runAfter": {},
                    "actions": {
                        "Approval": {
                            "type": "Approval",
                            "inputs": {
                                "title": "Glossary Term Creation Request",
                                "assignedTo": [
                                    # Add approver email addresses here
                                    "data-steward@yourdomain.com"
                                ]
                            },
                            "runAfter": {}
                        },
                        "Condition": {
                            "type": "If",
                            "expression": {
                                "and": [
                                    {
                                        "equals": [
                                            "@outputs('Approval')['outcome']",
                                            "Approved"
                                        ]
                                    }
                                ]
                            },
                            "actions": {
                                "Approved": {
                                    "type": "CreateTerm",
                                    "runAfter": {}
                                }
                            },
                            "runAfter": {
                                "Approval": ["Succeeded"]
                            }
                        }
                    }
                }
            }
        }
    }


def create_data_access_workflow():
    """
    Create a workflow for data access request approval.

    Returns:
        Dictionary with workflow configuration
    """
    return {
        "name": "Data Access Request Approval",
        "description": "Approve requests for data access",
        "triggers": [
            {
                "type": "when_data_access_request_submitted"
            }
        ],
        "isEnabled": True,
        "actionDag": {
            "actions": {
                "Start": {
                    "type": "Start",
                    "runAfter": {},
                    "actions": {
                        "Approval": {
                            "type": "Approval",
                            "inputs": {
                                "title": "Data Access Request",
                                "assignedTo": [
                                    "data-owner@yourdomain.com"
                                ]
                            },
                            "runAfter": {}
                        },
                        "Condition": {
                            "type": "If",
                            "expression": {
                                "and": [
                                    {
                                        "equals": [
                                            "@outputs('Approval')['outcome']",
                                            "Approved"
                                        ]
                                    }
                                ]
                            },
                            "actions": {
                                "GrantAccess": {
                                    "type": "GrantDataAccess",
                                    "runAfter": {}
                                }
                            },
                            "runAfter": {
                                "Approval": ["Succeeded"]
                            }
                        }
                    }
                }
            }
        }
    }


def main():
    """Create approval workflows."""

    # Setup
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set in environment")
        print("Copy .env.example to .env and configure your credentials")
        return

    print("Authenticating...")
    try:
        token = get_access_token()
        client = PurviewWorkflowClient(endpoint=endpoint, access_token=token)
        print("SUCCESS: Authenticated\n")
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        return

    # List existing workflows
    print("=" * 70)
    print("Step 1: List Existing Workflows")
    print("=" * 70)

    try:
        workflows = client.list_workflows()

        if workflows:
            print(f"\nFound {len(workflows)} existing workflows:\n")
            for wf in workflows:
                name = wf.get("name", "Unnamed")
                wf_id = wf.get("id")
                enabled = wf.get("isEnabled", False)
                status = "SUCCESS: Enabled" if enabled else "WARNING: Disabled"
                print(f"  - {name} ({status})")
                print(f"    ID: {wf_id}")
        else:
            print("\nNo existing workflows found.\n")

    except Exception as e:
        print(f"ERROR: Failed to list workflows: {e}")
        print("\nTroubleshooting:")
        print("  - Verify Workflow Admin role is assigned")
        print("  - Check that workflows feature is enabled in your Purview account\n")
        return

    # Choose workflow type
    print("\n" + "=" * 70)
    print("Step 2: Select Workflow Type")
    print("=" * 70)

    print("\nAvailable workflow types:")
    print("  1. Glossary Term Approval")
    print("  2. Data Access Request Approval")

    choice = input("\nSelect workflow type (1-2, or press Enter for #1): ").strip() or "1"

    if choice == "2":
        workflow_config = create_data_access_workflow()
        workflow_type = "Data Access Request"
    else:
        workflow_config = create_glossary_approval_workflow()
        workflow_type = "Glossary Term"

    # Customize approvers
    print("\n" + "=" * 70)
    print("Step 3: Configure Approvers")
    print("=" * 70)

    print(f"\nWorkflow: {workflow_config['name']}")
    print(f"Default approver: {workflow_config['actionDag']['actions']['Start']['actions']['Approval']['inputs']['assignedTo'][0]}")

    customize = input("\nCustomize approver email? (y/n): ").strip().lower()

    if customize == 'y':
        email = input("Enter approver email address: ").strip()
        if email:
            workflow_config['actionDag']['actions']['Start']['actions']['Approval']['inputs']['assignedTo'] = [email]
            print(f"SUCCESS: Updated approver to: {email}")

    # Create workflow
    print("\n" + "=" * 70)
    print("Step 4: Create Workflow")
    print("=" * 70)

    workflow_id = str(uuid.uuid4())
    print(f"\nWorkflow Name: {workflow_config['name']}")
    print(f"Workflow ID: {workflow_id}")
    print(f"Type: {workflow_type} Approval")

    confirm = input("\nCreate this workflow? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    try:
        result = client.create_or_replace_workflow(
            workflow_id=workflow_id,
            workflow_config=workflow_config
        )

        print("\nSUCCESS: Workflow created successfully!")
        print(f"Workflow ID: {result.get('id', workflow_id)}")
        print(f"Name: {result.get('name')}")
        print(f"Enabled: {result.get('isEnabled', False)}")

        print("\nWorkflow Details:")
        triggers = result.get('triggers', [])
        if triggers:
            print(f"  Triggers: {len(triggers)} trigger(s)")
            for trigger in triggers:
                print(f"    - {trigger.get('type', 'Unknown')}")

        print("\nNext Steps:")
        print("  - Test the workflow by triggering its action (e.g., create glossary term)")
        print("  - Check for pending approval tasks")
        print("  - View workflow runs in Purview Portal")
        print()

    except Exception as e:
        print(f"\nERROR: Failed to create workflow: {e}")
        print("\nTroubleshooting:")
        print("  - Verify Workflow Admin role is assigned")
        print("  - Check approver email addresses are valid")
        print("  - Ensure trigger type is supported in your Purview version")
        print("  - Verify glossary path exists (for glossary workflows)")
        print()

    print("=" * 70)
    print("SUCCESS: Workflow creation example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
