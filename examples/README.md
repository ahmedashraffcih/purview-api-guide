# Purview API Examples

This directory contains practical, working examples for Microsoft Purview REST APIs.

## Prerequisites

Before running examples:

1. **Configure credentials**: Copy `.env.example` to `.env` and fill in your credentials
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Assign RBAC roles**: See [Getting Started Guide](../docs/getting-started.md)

## Running Examples

All examples can be run directly with Python:

```bash
python examples/data-map/01_search_assets.py
```

## Examples by Category

### Data Map / Catalog Examples

Located in `data-map/`:

- **01_search_assets.py** - Search for data assets using keywords and filters
- **02_manage_classifications.py** - Add and manage classifications (PII, Confidential, etc.)
- **03_manage_labels.py** - Add free-text labels for organizing assets
- **04_business_metadata.py** - Set custom business metadata attributes
- **05_glossary_terms.py** - Create and manage glossary terms

**Common use cases:**
- Finding specific assets in your catalog
- Tagging sensitive data with classifications
- Adding business context to technical assets
- Building a business glossary

### Data Quality Examples

Located in `data-quality/`:

- **01_create_rules.py** - Create data quality rules from definitions
- **02_profile_assets.py** - Trigger data profiling jobs
- **03_monitor_quality.py** - Monitor quality assessment results

**Common use cases:**
- Automating quality rule creation
- Scheduling regular profiling
- Building quality dashboards

### Workflow Examples

Located in `workflow/`:

- **01_create_workflow.py** - Create approval workflows
- **02_approval_flow.py** - Handle approval requests
- **03_manage_tasks.py** - Manage workflow tasks

**Common use cases:**
- Implementing data access request workflows
- Creating glossary term approval processes
- Automating governance approvals

### Advanced Examples

Located in `advanced/`:

- **01_bulk_operations.py** - Bulk entity updates and operations
- **02_pagination.py** - Handle large result sets with pagination
- **03_error_handling.py** - Robust error handling patterns

**Common use cases:**
- Processing large numbers of assets
- Building production-grade integrations
- Handling API errors gracefully

## Example Structure

Each example follows this pattern:

```python
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token

def main():
    # Load configuration
    endpoint = os.getenv("PURVIEW_ENDPOINT")

    # Authenticate
    token = get_access_token()

    # Create client
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)

    # Use client...

if __name__ == "__main__":
    main()
```

## Customizing Examples

All examples use environment variables for configuration. No hardcoded values!

To use with your own data:
1. Update `.env` with your Purview endpoint and credentials
2. Run the example
3. Follow prompts to select your assets

## Error Handling

If you encounter errors:

1. **401 Unauthorized**: Check credentials in `.env`
2. **403 Forbidden**: Verify RBAC role assignments
3. **404 Not Found**: Verify endpoint URL format
4. **429 Too Many Requests**: Wait and retry (automatic in clients)

See [Troubleshooting Guide](../docs/troubleshooting.md) for detailed solutions.

## Official Documentation

- [Purview REST API Reference](https://learn.microsoft.com/en-us/rest/api/purview/)
- [Data Map API](https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane)
- [Data Quality API](https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane)
- [Workflow API](https://learn.microsoft.com/en-us/rest/api/purview/workflowdataplane)

## Contributing

Found a useful pattern? Share it!

1. Create a new example following the structure above
2. Add comprehensive comments
3. Test with clean credentials
4. Submit a PR

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
