"""
Client for Microsoft Purview Workflow APIs.

Provides methods for:
- Creating and managing approval workflows
- Submitting user requests
- Approving/rejecting workflow tasks
- Monitoring workflow runs

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane
"""

from typing import Any, Dict, List, Optional
from clients.base_client import BaseHTTPClient


class PurviewWorkflowClient(BaseHTTPClient):
    """
    Client for Purview Workflow APIs.

    Workflows enable approval processes for data access requests, glossary term
    submissions, and other governance actions.

    Example:
        >>> from clients.workflow_client import PurviewWorkflowClient
        >>> from clients.auth import get_access_token
        >>> import os
        >>>
        >>> token = get_access_token()
        >>> endpoint = os.getenv("PURVIEW_ENDPOINT")
        >>> client = PurviewWorkflowClient(endpoint=endpoint, access_token=token)
        >>>
        >>> # List workflows
        >>> workflows = client.list_workflows()
        >>> print(f"Found {len(workflows)} workflows")

    Official documentation:
    https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflows
    """

    def __init__(
        self,
        endpoint: str,
        access_token: str,
        api_version: str = "2023-10-01-preview"
    ):
        """
        Initialize Workflow client.

        Args:
            endpoint: Purview account endpoint (e.g., https://account.purview.azure.com)
            access_token: OAuth2 bearer token (from get_access_token())
            api_version: API version (default: 2023-10-01-preview)
        """
        super().__init__(base_url=endpoint, access_token=access_token)
        self.api_version = api_version

    # ===== Workflow Management =====

    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all workflows in the account.

        Returns:
            List of workflow dictionaries with id, name, description, triggers, etc.

        Example:
            >>> workflows = client.list_workflows()
            >>> for wf in workflows:
            ...     print(f"{wf['name']}: {wf['id']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflows/list
        """
        response = self.get(
            "/workflow/workflows",
            params={"api-version": self.api_version}
        )
        return response.json().get("value", [])

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow details by ID.

        Args:
            workflow_id: Workflow GUID

        Returns:
            Workflow dictionary with full configuration

        Example:
            >>> workflow = client.get_workflow("workflow-guid")
            >>> print(f"Workflow: {workflow['name']}")
            >>> print(f"Triggers: {workflow['triggers']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflows/get
        """
        response = self.get(
            f"/workflow/workflows/{workflow_id}",
            params={"api-version": self.api_version}
        )
        return response.json()

    def create_or_replace_workflow(
        self,
        workflow_id: str,
        workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create or replace a workflow.

        Args:
            workflow_id: Workflow GUID (generate new GUID for new workflows)
            workflow_config: Workflow configuration dictionary

        Returns:
            Created/updated workflow dictionary

        Example:
            >>> import uuid
            >>> workflow = client.create_or_replace_workflow(
            ...     workflow_id=str(uuid.uuid4()),
            ...     workflow_config={
            ...         "name": "Glossary Term Approval",
            ...         "description": "Approve new glossary term submissions",
            ...         "triggers": [
            ...             {
            ...                 "type": "when_term_creation_is_requested",
            ...                 "underGlossaryHierarchy": "/glossaries/business-glossary"
            ...             }
            ...         ],
            ...         "isEnabled": True,
            ...         "actionDag": {
            ...             "actions": {
            ...                 "Start": {
            ...                     "type": "Start",
            ...                     "runAfter": {},
            ...                     "actions": {
            ...                         "Approval": {
            ...                             "type": "Approval",
            ...                             "inputs": {
            ...                                 "assignedTo": ["user@domain.com"]
            ...                             }
            ...                         }
            ...                     }
            ...                 }
            ...             }
            ...         }
            ...     }
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflows/create-or-replace
        """
        response = self.put(
            f"/workflow/workflows/{workflow_id}",
            json=workflow_config,
            params={"api-version": self.api_version}
        )
        return response.json()

    def delete_workflow(self, workflow_id: str) -> None:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow GUID

        Example:
            >>> client.delete_workflow("workflow-guid")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflows/delete
        """
        self.delete(
            f"/workflow/workflows/{workflow_id}",
            params={"api-version": self.api_version}
        )

    # ===== User Requests =====

    def submit_user_request(
        self,
        workflow_id: str,
        request_payload: Dict[str, Any]
    ) -> str:
        """
        Submit a user request to trigger a workflow.

        Args:
            workflow_id: Workflow GUID
            request_payload: Request payload (structure depends on workflow trigger type)

        Returns:
            Request ID (GUID)

        Example:
            >>> request_id = client.submit_user_request(
            ...     workflow_id="workflow-guid",
            ...     request_payload={
            ...         "type": "CreateTerm",
            ...         "term": {
            ...             "name": "Customer Churn Rate",
            ...             "description": "Percentage of customers who cancel service"
            ...         }
            ...     }
            ... )
            >>> print(f"Request submitted: {request_id}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/user-requests/submit
        """
        response = self.post(
            "/workflow/userrequests",
            json={"workflowId": workflow_id, "payload": request_payload},
            params={"api-version": self.api_version}
        )
        result = response.json()
        return result.get("id")

    # ===== Task Management =====

    def list_tasks(
        self,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List workflow tasks (pending approvals).

        Args:
            workflow_id: Optional filter by workflow ID
            workflow_run_id: Optional filter by specific workflow run

        Returns:
            List of task dictionaries

        Example:
            >>> tasks = client.list_tasks(workflow_id="workflow-guid")
            >>> for task in tasks:
            ...     print(f"Task {task['id']}: {task['status']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-tasks/list
        """
        params = {"api-version": self.api_version}
        if workflow_id:
            params["workflowId"] = workflow_id
        if workflow_run_id:
            params["workflowRunId"] = workflow_run_id

        response = self.get("/workflow/workflowtasks", params=params)
        return response.json().get("value", [])

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get task details by ID.

        Args:
            task_id: Task GUID

        Returns:
            Task dictionary with status, payload, approvers, etc.

        Example:
            >>> task = client.get_task("task-guid")
            >>> print(f"Task status: {task['status']}")
            >>> print(f"Request: {task['requestor']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-tasks/get
        """
        response = self.get(
            f"/workflow/workflowtasks/{task_id}",
            params={"api-version": self.api_version}
        )
        return response.json()

    def approve_task(
        self,
        task_id: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a workflow task.

        Args:
            task_id: Task GUID
            comment: Optional approval comment

        Returns:
            Approval response dictionary

        Example:
            >>> result = client.approve_task(
            ...     task_id="task-guid",
            ...     comment="Approved - meets data quality standards"
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-tasks/approve
        """
        body = {"comment": comment} if comment else {}

        response = self.post(
            f"/workflow/workflowtasks/{task_id}/approve",
            json=body,
            params={"api-version": self.api_version}
        )
        return response.json()

    def reject_task(
        self,
        task_id: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject a workflow task.

        Args:
            task_id: Task GUID
            comment: Optional rejection reason

        Returns:
            Rejection response dictionary

        Example:
            >>> result = client.reject_task(
            ...     task_id="task-guid",
            ...     comment="Rejected - insufficient documentation"
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-tasks/reject
        """
        body = {"comment": comment} if comment else {}

        response = self.post(
            f"/workflow/workflowtasks/{task_id}/reject",
            json=body,
            params={"api-version": self.api_version}
        )
        return response.json()

    # ===== Workflow Runs =====

    def list_workflow_runs(
        self,
        workflow_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List workflow run history.

        Args:
            workflow_id: Optional filter by workflow ID

        Returns:
            List of workflow run dictionaries with status, timestamps, etc.

        Example:
            >>> runs = client.list_workflow_runs(workflow_id="workflow-guid")
            >>> for run in runs:
            ...     print(f"Run {run['id']}: {run['status']} ({run['startTime']})")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-runs/list
        """
        params = {"api-version": self.api_version}
        if workflow_id:
            params["workflowId"] = workflow_id

        response = self.get("/workflow/workflowruns", params=params)
        return response.json().get("value", [])

    def get_workflow_run(self, run_id: str) -> Dict[str, Any]:
        """
        Get workflow run details.

        Args:
            run_id: Workflow run GUID

        Returns:
            Workflow run dictionary with full execution details

        Example:
            >>> run = client.get_workflow_run("run-guid")
            >>> print(f"Status: {run['status']}")
            >>> print(f"Duration: {run['endTime'] - run['startTime']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-runs/get
        """
        response = self.get(
            f"/workflow/workflowruns/{run_id}",
            params={"api-version": self.api_version}
        )
        return response.json()

    def cancel_workflow_run(self, run_id: str, comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a running workflow.

        Args:
            run_id: Workflow run GUID
            comment: Optional cancellation reason

        Returns:
            Cancellation response dictionary

        Example:
            >>> result = client.cancel_workflow_run(
            ...     run_id="run-guid",
            ...     comment="Requester withdrew request"
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane/workflow-runs/cancel
        """
        body = {"comment": comment} if comment else {}

        response = self.post(
            f"/workflow/workflowruns/{run_id}/cancel",
            json=body,
            params={"api-version": self.api_version}
        )
        return response.json()
