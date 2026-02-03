# Workflow API Guide

The Workflow API enables you to create and manage approval workflows for governance actions like glossary term creation, data access requests, and custom integrations.

## Official Documentation

- [Workflow API Reference](https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane)
- [Workflow Concepts](https://learn.microsoft.com/en-us/purview/concept-workflow)

## Authentication & Authorization

**Endpoint**: `https://<your-account>.purview.azure.com/workflow/`

**Required Roles**:
- **Workflow Admin**: Create, update, delete workflows
- **Workflow Approver**: Approve/reject workflow tasks
- **Workflow User**: Submit user requests

Assign roles at: **Purview Portal** → **Management** → **Role assignments**

## Client Setup

```python
from clients.workflow_client import PurviewWorkflowClient
from clients.auth import get_access_token
import os

# Authenticate
token = get_access_token()

# Create client
client = PurviewWorkflowClient(
    endpoint=os.getenv("PURVIEW_ENDPOINT"),
    access_token=token,
    api_version="2023-10-01-preview"  # Default
)
```

## Core Concepts

### Workflows
Automated approval processes triggered by governance actions.

### Triggers
Events that start a workflow (e.g., glossary term creation, data access request).

### Action DAG
Directed Acyclic Graph of actions to execute (Start → Approval → Condition → Action).

### Tasks
Approval requests created by workflows and assigned to approvers.

### User Requests
Manual submissions that trigger workflows.

## Common Operations

### 1. List Workflows

```python
# Get all workflows
workflows = client.list_workflows()

for wf in workflows:
    print(f"Workflow: {wf['name']}")
    print(f"  ID: {wf['id']}")
    print(f"  Enabled: {wf['isEnabled']}")
    print(f"  Triggers: {wf['triggers']}")
```

### 2. Get Workflow Details

```python
# Get specific workflow
workflow = client.get_workflow(workflow_id="workflow-guid")

print(f"Name: {workflow['name']}")
print(f"Description: {workflow['description']}")
print(f"Enabled: {workflow['isEnabled']}")

# View trigger configuration
for trigger in workflow['triggers']:
    print(f"Trigger: {trigger['type']}")

# View action configuration
action_dag = workflow['actionDag']
print(f"Actions: {list(action_dag['actions'].keys())}")
```

### 3. Create Glossary Approval Workflow

Create a workflow that requires approval before creating glossary terms.

```python
import uuid

workflow_id = str(uuid.uuid4())

workflow = client.create_or_replace_workflow(
    workflow_id=workflow_id,
    workflow_config={
        "name": "Glossary Term Approval",
        "description": "Require approval for new glossary terms",
        "triggers": [
            {
                "type": "when_term_creation_is_requested",
                "underGlossaryHierarchy": "/glossaries/Glossary"
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
                                "assignedTo": ["approver@company.com"]
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
                                "CreateTerm": {
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
)

print(f"Workflow created: {workflow['id']}")
```

### 4. Create Data Access Approval Workflow

Create a workflow for approving data access requests.

```python
workflow = client.create_or_replace_workflow(
    workflow_id=str(uuid.uuid4()),
    workflow_config={
        "name": "Data Access Request Approval",
        "description": "Approve data access requests",
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
                                "assignedTo": ["data-owner@company.com"]
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
)
```

### 5. Workflow Trigger Types

Common trigger types:

- `when_term_creation_is_requested` - Glossary term creation
- `when_term_update_is_requested` - Glossary term updates
- `when_term_deletion_is_requested` - Glossary term deletion
- `when_data_access_request_submitted` - Data access requests
- `when_asset_update_is_requested` - Asset metadata updates

### 6. Submit User Request

Trigger a workflow by submitting a user request.

```python
# Submit request to create glossary term
request_id = client.submit_user_request(
    workflow_id="workflow-guid",
    request_payload={
        "type": "CreateTerm",
        "term": {
            "name": "Customer Lifetime Value",
            "description": "Total revenue expected from a customer",
            "glossaryId": "glossary-guid"
        }
    }
)

print(f"Request submitted: {request_id}")
```

**Note**: Request payload structure depends on the workflow trigger type. Some triggers may not support API submission.

### 7. List Pending Tasks

Get all pending approval tasks.

```python
# List all tasks
tasks = client.list_tasks()

for task in tasks:
    print(f"Task: {task['id']}")
    print(f"  Type: {task['type']}")
    print(f"  Status: {task['status']}")
    print(f"  Requestor: {task['requestor']}")

# Filter by workflow
workflow_tasks = client.list_tasks(workflow_id="workflow-guid")
```

### 8. Get Task Details

Retrieve full task information including request payload.

```python
# Get task details
task = client.get_task(task_id="task-guid")

print(f"Task ID: {task['id']}")
print(f"Status: {task['status']}")
print(f"Workflow ID: {task['workflowId']}")
print(f"Requestor: {task['requestor']}")
print(f"Created: {task['createdTime']}")

# View request payload
payload = task['payload']
print(f"Request details: {payload}")

# View assigned approvers
approvers = task.get('approvers', [])
print(f"Assigned to: {', '.join(approvers)}")
```

### 9. Approve Task

Approve a pending workflow task.

```python
# Approve with comment
result = client.approve_task(
    task_id="task-guid",
    comment="Approved - meets data governance standards"
)

print("Task approved successfully")
```

### 10. Reject Task

Reject a pending workflow task.

```python
# Reject with comment
result = client.reject_task(
    task_id="task-guid",
    comment="Rejected - insufficient business justification"
)

print("Task rejected successfully")
```

### 11. Update Workflow

Modify an existing workflow (same method as create).

```python
# Update workflow configuration
updated_workflow = client.create_or_replace_workflow(
    workflow_id="existing-workflow-guid",
    workflow_config={
        # Updated configuration
        "name": "Updated Workflow Name",
        # ... rest of configuration
    }
)
```

### 12. Delete Workflow

Remove a workflow.

```python
# Delete workflow
client.delete_workflow(workflow_id="workflow-guid")
print("Workflow deleted")
```

## Action DAG Structure

The Action DAG defines the workflow execution logic:

```python
{
    "actions": {
        "Start": {  # Entry point
            "type": "Start",
            "runAfter": {},
            "actions": {
                "Approval": {  # Approval action
                    "type": "Approval",
                    "inputs": {
                        "title": "Approval Title",
                        "assignedTo": ["user1@company.com", "user2@company.com"]
                    },
                    "runAfter": {}
                },
                "Condition": {  # Conditional logic
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
                        "ApprovedAction": {
                            "type": "CreateTerm",  # Action on approval
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
```

**Action Types**:
- `Start` - Workflow entry point
- `Approval` - Request approval from users
- `If` - Conditional branching
- `CreateTerm` - Create glossary term
- `GrantDataAccess` - Grant data access
- Custom actions (extensible)

## Task Status Values

- `Pending` - Awaiting approval
- `Approved` - Task approved
- `Rejected` - Task rejected
- `Cancelled` - Task cancelled
- `InProgress` - Task being processed

## Bulk Task Management

Process multiple tasks efficiently:

```python
# Approve all pending tasks for a workflow
tasks = client.list_tasks(workflow_id="workflow-guid")

for task in tasks:
    if task['status'] == 'Pending':
        try:
            client.approve_task(
                task_id=task['id'],
                comment="Bulk approved"
            )
            print(f"✅ Approved {task['id']}")
        except Exception as e:
            print(f"❌ Failed {task['id']}: {e}")
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Missing Workflow Admin role | Assign Workflow Admin role |
| 404 Not Found | Invalid workflow or task ID | Verify ID exists |
| 400 Bad Request | Invalid workflow configuration | Check action DAG structure |
| Task not found | Task already processed or cancelled | Check task status first |
| Invalid approver | Email address not valid in Azure AD | Use valid UPNs |

See [Troubleshooting Guide](troubleshooting.md) for detailed solutions.

## Known Limitations

1. **Some triggers don't support API submission** - Must be triggered through Portal UI
2. **Workflow configuration is complex** - Test in Portal UI first, then export to API
3. **Limited workflow run history via API** - Use Portal for detailed run logs
4. **No workflow validation endpoint** - Invalid configs fail at runtime

See [API Limitations](api-limitations.md) for complete list.

## Examples

Complete working examples:

- [01_create_workflow.py](../examples/workflow/01_create_workflow.py) - Create approval workflows
- [02_approval_flow.py](../examples/workflow/02_approval_flow.py) - Complete approval flow
- [03_manage_tasks.py](../examples/workflow/03_manage_tasks.py) - Task management operations

## Best Practices

1. **Test workflows in Portal first** - Validate configuration before API automation
2. **Use meaningful names and descriptions** - Makes management easier
3. **Set up email notifications** - Configure in Portal for approver alerts
4. **Add clear approval comments** - Document decision rationale
5. **Monitor task queue regularly** - Prevent approval backlogs
6. **Implement error handling** - Tasks may fail or be cancelled
7. **Use workflow filters** - Focus on specific workflows when listing tasks

## Integration Patterns

### Automated Approval Logic

```python
# Auto-approve based on business rules
tasks = client.list_tasks(workflow_id="workflow-guid")

for task in tasks:
    payload = task['payload']

    # Apply business logic
    if meets_auto_approval_criteria(payload):
        client.approve_task(
            task_id=task['id'],
            comment="Auto-approved - meets criteria"
        )
    else:
        # Leave for manual review
        print(f"Manual review required: {task['id']}")
```

### Workflow Monitoring Dashboard

```python
# Get workflow statistics
workflows = client.list_workflows()

for wf in workflows:
    tasks = client.list_tasks(workflow_id=wf['id'])
    pending = len([t for t in tasks if t['status'] == 'Pending'])

    print(f"{wf['name']}: {pending} pending tasks")
```

## Next Steps

- [Data Map API Guide](data-map-api.md) - Search and manage assets
- [Data Quality API Guide](data-quality-api.md) - Quality rules and profiling
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
