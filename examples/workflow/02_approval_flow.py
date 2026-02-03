"""
Example: Workflow Approval Flow

This example demonstrates the complete approval flow:
1. List workflows
2. Submit a user request to trigger a workflow
3. Monitor workflow run status
4. List pending approval tasks
5. Approve or reject tasks

Prerequisites:
- Service principal with Workflow Admin role
- .env file configured with credentials
- At least one workflow created (use 01_create_workflow.py)

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.workflow_client import PurviewWorkflowClient
from clients.auth import get_access_token


def main():
    """Demonstrate complete workflow approval flow."""

    # Setup
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set in environment")
        return

    print("Authenticating...")
    try:
        token = get_access_token()
        client = PurviewWorkflowClient(endpoint=endpoint, access_token=token)
        print("SUCCESS: Authenticated\n")
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        return

    # Step 1: List workflows
    print("=" * 70)
    print("Step 1: Select Workflow")
    print("=" * 70)

    try:
        workflows = client.list_workflows()

        if not workflows:
            print("ERROR: No workflows found.")
            print("\nCreate a workflow first using: examples/workflow/01_create_workflow.py")
            return

        print(f"\nFound {len(workflows)} workflows:\n")

        # Filter to enabled workflows only
        enabled_workflows = [wf for wf in workflows if wf.get("isEnabled", False)]

        if not enabled_workflows:
            print("WARNING: No enabled workflows found.")
            print("\nEnable a workflow in the Purview Portal or create a new one.")
            return

        for i, wf in enumerate(enabled_workflows, 1):
            name = wf.get("name", "Unnamed")
            wf_id = wf.get("id")
            triggers = wf.get("triggers", [])
            trigger_types = [t.get("type", "Unknown") for t in triggers]

            print(f"{i}. {name}")
            print(f"   ID: {wf_id}")
            print(f"   Triggers: {', '.join(trigger_types)}")
            print()

        choice = input(f"Select workflow (1-{len(enabled_workflows)}, or press Enter for #1): ").strip() or "1"
        selected_workflow = enabled_workflows[int(choice) - 1 if choice.isdigit() else 0]

        workflow_id = selected_workflow["id"]
        workflow_name = selected_workflow.get("name", "Unnamed")

        print(f"\nSUCCESS: Selected: {workflow_name}")
        print(f"   ID: {workflow_id}\n")

    except Exception as e:
        print(f"ERROR: Failed to list workflows: {e}")
        return

    # Step 2: Submit user request
    print("=" * 70)
    print("Step 2: Submit User Request")
    print("=" * 70)

    print(f"\nThis will trigger the workflow: {workflow_name}")
    print("\nNote: The request payload structure depends on the workflow trigger type.")

    # Determine trigger type and create appropriate payload
    triggers = selected_workflow.get("triggers", [])
    if triggers:
        trigger_type = triggers[0].get("type", "")

        if "term_creation" in trigger_type.lower():
            print("\nThis is a glossary term creation workflow.")
            term_name = input("Enter glossary term name: ").strip() or "Sample Term"
            term_desc = input("Enter term description: ").strip() or "Sample description"

            request_payload = {
                "type": "CreateTerm",
                "term": {
                    "name": term_name,
                    "description": term_desc,
                    "glossaryId": "<glossary-guid>"  # Would need to be provided
                }
            }
            print(f"\nPayload: Create term '{term_name}'")

        elif "data_access" in trigger_type.lower():
            print("\nThis is a data access request workflow.")
            asset_name = input("Enter asset name: ").strip() or "Sample Asset"

            request_payload = {
                "type": "DataAccessRequest",
                "assetName": asset_name,
                "requestor": "user@domain.com",
                "justification": "Need access for analysis"
            }
            print(f"\nPayload: Request access to '{asset_name}'")

        else:
            print(f"\nUnknown trigger type: {trigger_type}")
            print("Creating generic request payload...")
            request_payload = {
                "type": "GenericRequest",
                "description": "Test workflow request"
            }

    else:
        print("\nNo triggers found. Creating generic payload...")
        request_payload = {
            "type": "GenericRequest",
            "description": "Test workflow request"
        }

    submit = input("\nSubmit this request? (y/n): ").strip().lower()
    if submit != 'y':
        print("Skipping request submission.")
        request_id = None
    else:
        try:
            request_id = client.submit_user_request(
                workflow_id=workflow_id,
                request_payload=request_payload
            )

            print(f"\nSUCCESS: Request submitted successfully!")
            print(f"Request ID: {request_id}")

            print("\nThe workflow will now:")
            print("  1. Create a pending approval task")
            print("  2. Notify assigned approvers")
            print("  3. Wait for approval/rejection")
            print()

        except Exception as e:
            print(f"\nERROR: Failed to submit request: {e}")
            print("\nThis may be because:")
            print("  - The workflow trigger doesn't support API submission")
            print("  - The payload structure doesn't match workflow expectations")
            print("  - The workflow is disabled")
            print("\nContinuing with task management examples...\n")
            request_id = None

    # Step 3: List pending tasks
    print("=" * 70)
    print("Step 3: List Pending Approval Tasks")
    print("=" * 70)

    # Wait a moment for task to be created
    if request_id:
        print("\nWaiting 5 seconds for task creation...")
        time.sleep(5)

    try:
        tasks = client.list_tasks(workflow_id=workflow_id)

        if not tasks:
            print("\nWARNING: No pending tasks found for this workflow.")
            print("\nTasks may appear when:")
            print("  - A user request triggers the workflow")
            print("  - The workflow is manually triggered in Purview Portal")
            print()
        else:
            print(f"\nFound {len(tasks)} pending task(s):\n")

            for i, task in enumerate(tasks, 1):
                task_id = task.get("id")
                task_type = task.get("type", "Unknown")
                status = task.get("status", "Unknown")
                requestor = task.get("requestor", "Unknown")
                created = task.get("createdTime", "N/A")

                print(f"{i}. Task {task_id}")
                print(f"   Type: {task_type}")
                print(f"   Status: {status}")
                print(f"   Requestor: {requestor}")
                print(f"   Created: {created}")
                print()

            # Step 4: Approve/Reject a task
            print("=" * 70)
            print("Step 4: Approve or Reject Task")
            print("=" * 70)

            choice = input(f"\nSelect task to review (1-{len(tasks)}, or press Enter to skip): ").strip()

            if choice.isdigit() and 1 <= int(choice) <= len(tasks):
                selected_task = tasks[int(choice) - 1]
                task_id = selected_task["id"]

                # Get full task details
                print(f"\nFetching task details...")
                task_details = client.get_task(task_id)

                print(f"\nTask ID: {task_id}")
                print(f"Type: {task_details.get('type')}")
                print(f"Status: {task_details.get('status')}")
                print(f"Requestor: {task_details.get('requestor', 'N/A')}")

                payload = task_details.get("payload", {})
                if payload:
                    print(f"\nRequest Details:")
                    for key, value in payload.items():
                        print(f"  {key}: {value}")

                action = input("\nApprove or Reject? (a/r/skip): ").strip().lower()

                if action == 'a':
                    comment = input("Enter approval comment (optional): ").strip() or "Approved via API"

                    try:
                        result = client.approve_task(task_id=task_id, comment=comment)
                        print(f"\nSUCCESS: Task approved successfully!")
                        print(f"Comment: {comment}")

                    except Exception as e:
                        print(f"\nERROR: Failed to approve task: {e}")

                elif action == 'r':
                    comment = input("Enter rejection comment: ").strip() or "Rejected via API"

                    try:
                        result = client.reject_task(task_id=task_id, comment=comment)
                        print(f"\nSUCCESS: Task rejected successfully!")
                        print(f"Comment: {comment}")

                    except Exception as e:
                        print(f"\nERROR: Failed to reject task: {e}")

                else:
                    print("Skipped.")

    except Exception as e:
        print(f"ERROR: Failed to list tasks: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    print(f"\nWorkflow: {workflow_name}")
    if request_id:
        print(f"Request ID: {request_id}")
    print("\nNext Steps:")
    print("  - View workflow runs in Purview Portal")
    print("  - Check workflow execution history")
    print("  - Monitor approval task outcomes")
    print("  - Set up email notifications for approvers")

    print("\n" + "=" * 70)
    print("SUCCESS: Approval flow example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
