"""
Example: Manage Workflow Tasks

This example demonstrates workflow task management operations:
- List all pending tasks
- Filter tasks by workflow
- Get task details
- Approve/reject tasks in bulk
- Monitor task status

Prerequisites:
- Service principal with Workflow Admin role
- .env file configured with credentials
- Active workflows with pending tasks

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-tasks
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.workflow_client import PurviewWorkflowClient
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
    """Manage workflow approval tasks."""

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

    # Step 1: List all pending tasks
    print("=" * 70)
    print("Step 1: View All Pending Tasks")
    print("=" * 70)

    try:
        all_tasks = client.list_tasks()

        if not all_tasks:
            print("\nINFO: No pending tasks found!")
            print("\nTasks appear when:")
            print("  - User requests trigger workflows")
            print("  - Manual workflow submissions")
            print("  - Scheduled workflow executions")
            print("\nCreate a workflow and submit a request to generate tasks.")
            return

        print(f"\nFound {len(all_tasks)} pending task(s):\n")

        for i, task in enumerate(all_tasks, 1):
            task_id = task.get("id")
            task_type = task.get("type", "Unknown")
            status = task.get("status", "Unknown")
            workflow_id = task.get("workflowId", "N/A")
            requestor = task.get("requestor", "Unknown")
            created = format_timestamp(task.get("createdTime"))

            print(f"{i}. Task {task_id[:8]}...")
            print(f"   Type: {task_type}")
            print(f"   Status: {status}")
            print(f"   Workflow: {workflow_id[:8]}...")
            print(f"   Requestor: {requestor}")
            print(f"   Created: {created}")
            print()

    except Exception as e:
        print(f"ERROR: Failed to list tasks: {e}")
        return

    # Step 2: Group tasks by workflow
    print("=" * 70)
    print("Step 2: Group Tasks by Workflow")
    print("=" * 70)

    workflows = {}
    for task in all_tasks:
        wf_id = task.get("workflowId", "Unknown")
        if wf_id not in workflows:
            workflows[wf_id] = []
        workflows[wf_id].append(task)

    print(f"\nTasks grouped by {len(workflows)} workflow(s):\n")

    try:
        workflow_details = client.list_workflows()
        workflow_names = {wf["id"]: wf["name"] for wf in workflow_details}
    except:
        workflow_names = {}

    for wf_id, tasks in workflows.items():
        wf_name = workflow_names.get(wf_id, "Unknown Workflow")
        print(f"Workflow: {wf_name}")
        print(f"  ID: {wf_id}")
        print(f"  Pending Tasks: {len(tasks)}")
        print()

    # Step 3: Filter tasks by workflow
    print("=" * 70)
    print("Step 3: Filter Tasks by Workflow")
    print("=" * 70)

    if len(workflows) > 1:
        print("\nAvailable workflows:")
        workflow_list = list(workflows.keys())
        for i, wf_id in enumerate(workflow_list, 1):
            wf_name = workflow_names.get(wf_id, "Unknown")
            count = len(workflows[wf_id])
            print(f"  {i}. {wf_name} ({count} tasks)")

        choice = input(f"\nSelect workflow to view tasks (1-{len(workflow_list)}, or Enter to skip): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(workflow_list):
            selected_wf_id = workflow_list[int(choice) - 1]
            filtered_tasks = client.list_tasks(workflow_id=selected_wf_id)

            print(f"\n{len(filtered_tasks)} task(s) for this workflow:\n")
            for i, task in enumerate(filtered_tasks, 1):
                print(f"{i}. Task {task['id'][:8]}... - Status: {task.get('status')}")

            print()
        else:
            filtered_tasks = all_tasks
    else:
        filtered_tasks = all_tasks

    # Step 4: View task details
    print("=" * 70)
    print("Step 4: View Task Details")
    print("=" * 70)

    choice = input(f"\nSelect task to view details (1-{len(filtered_tasks)}, or Enter to skip): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(filtered_tasks):
        selected_task = filtered_tasks[int(choice) - 1]
        task_id = selected_task["id"]

        try:
            task_details = client.get_task(task_id)

            print(f"\n{'=' * 50}")
            print("Task Details")
            print('=' * 50)
            print(f"ID: {task_id}")
            print(f"Type: {task_details.get('type', 'Unknown')}")
            print(f"Status: {task_details.get('status', 'Unknown')}")
            print(f"Workflow ID: {task_details.get('workflowId', 'N/A')}")
            print(f"Workflow Run ID: {task_details.get('workflowRunId', 'N/A')}")
            print(f"Requestor: {task_details.get('requestor', 'Unknown')}")
            print(f"Created: {format_timestamp(task_details.get('createdTime'))}")
            print(f"Updated: {format_timestamp(task_details.get('lastUpdateTime'))}")

            # Show payload
            payload = task_details.get("payload", {})
            if payload:
                print(f"\nRequest Payload:")
                for key, value in payload.items():
                    print(f"  {key}: {value}")

            # Show assigned approvers
            approvers = task_details.get("approvers", [])
            if approvers:
                print(f"\nAssigned Approvers:")
                for approver in approvers:
                    print(f"  - {approver}")

            print()

        except Exception as e:
            print(f"\nERROR: Failed to get task details: {e}\n")

    # Step 5: Bulk approve/reject
    print("=" * 70)
    print("Step 5: Bulk Task Actions")
    print("=" * 70)

    print(f"\nYou have {len(filtered_tasks)} pending task(s).")
    print("\nBulk actions:")
    print("  1. Approve all tasks")
    print("  2. Reject all tasks")
    print("  3. Skip")

    action = input("\nSelect action (1-3, or Enter to skip): ").strip()

    if action == "1":
        comment = input("Enter approval comment (optional): ").strip() or "Bulk approved via API"
        confirm = input(f"\nApprove {len(filtered_tasks)} task(s)? (y/n): ").strip().lower()

        if confirm == 'y':
            success_count = 0
            fail_count = 0

            for task in filtered_tasks:
                try:
                    client.approve_task(task_id=task["id"], comment=comment)
                    success_count += 1
                    print(f"SUCCESS: Approved task {task['id'][:8]}...")
                except Exception as e:
                    fail_count += 1
                    print(f"ERROR: Failed to approve {task['id'][:8]}...: {e}")

            print(f"\nResults: {success_count} approved, {fail_count} failed")

    elif action == "2":
        comment = input("Enter rejection comment: ").strip() or "Bulk rejected via API"
        confirm = input(f"\nReject {len(filtered_tasks)} task(s)? (y/n): ").strip().lower()

        if confirm == 'y':
            success_count = 0
            fail_count = 0

            for task in filtered_tasks:
                try:
                    client.reject_task(task_id=task["id"], comment=comment)
                    success_count += 1
                    print(f"SUCCESS: Rejected task {task['id'][:8]}...")
                except Exception as e:
                    fail_count += 1
                    print(f"ERROR: Failed to reject {task['id'][:8]}...: {e}")

            print(f"\nResults: {success_count} rejected, {fail_count} failed")

    else:
        print("Skipped.")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    print(f"\nTotal Pending Tasks: {len(all_tasks)}")
    print(f"Workflows with Tasks: {len(workflows)}")

    print("\nTask Management Tips:")
    print("  - Set up email notifications for approvers")
    print("  - Use filters to focus on specific workflows")
    print("  - Add meaningful comments when approving/rejecting")
    print("  - Monitor workflow execution logs in Purview Portal")
    print("  - Consider automating routine approvals with logic")

    print("\n" + "=" * 70)
    print("SUCCESS: Task management example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
