# Microsoft Purview REST API Guide

> ⚠️ **UNOFFICIAL COMMUNITY RESOURCE** ⚠️
> This is an **unofficial, community-maintained** guide for working with Microsoft Purview REST APIs. It is **not affiliated with, endorsed by, or supported by Microsoft**. For official documentation, please visit [Microsoft Learn](https://learn.microsoft.com/en-us/purview/).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

## Overview

A comprehensive, production-ready guide for working with Microsoft Purview REST APIs. This repository provides clean Python client implementations, real-world examples, and detailed documentation for:

- 🗺️ **Data Map API** (Atlas) - Search, entity management, classifications, labels, glossaries
- ✅ **Data Quality API** - Quality rules, profiling, assessments
- 🔄 **Workflow API** - Approval workflows, task management
- 📚 **Catalog API** - Data catalog operations

## Why This Guide?

Microsoft Purview offers powerful REST APIs, but working with them can be challenging:
- Complex authentication flows
- Undocumented API limitations and workarounds
- Scattered examples across different documentation sources
- Inconsistent API versions and endpoints

This guide consolidates community knowledge, real-world solutions, and production-tested code to help you succeed faster.

## Quick Start

### 1. Prerequisites

- Azure subscription with a Microsoft Purview account
- Service principal (app registration) with appropriate Purview RBAC roles
- Python 3.8 or higher

### 2. Installation

```bash
git clone https://github.com/ahmedashraffcih/purview-api-guide.git
cd purview-api-guide
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your service principal credentials
```

### 4. Run Your First Example

```bash
python examples/data-map/01_search_assets.py
```

## Documentation

📖 **[Getting Started Guide](docs/getting-started.md)** - Setup, authentication, RBAC requirements

📖 **[Data Map API Guide](docs/data-map-api.md)** - Search, entities, classifications, labels, business metadata

📖 **[Data Quality API Guide](docs/data-quality-api.md)** - Quality rules, profiling, monitoring

📖 **[Workflow API Guide](docs/workflow-api.md)** - Create workflows, manage approvals

📖 **[API Limitations](docs/api-limitations.md)** - Known issues, workarounds, gotchas

📖 **[Troubleshooting](docs/troubleshooting.md)** - Common errors and solutions

## Client Library

Production-ready Python clients with:
- ✅ Service principal authentication with automatic token refresh
- ✅ Retry logic for rate limiting and transient errors
- ✅ Comprehensive docstrings with links to official documentation
- ✅ Type hints throughout
- ✅ Clean error messages with troubleshooting guidance

```python
from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token

# Authenticate
token = get_access_token()

# Create client
client = PurviewDataMapClient(
    endpoint="https://your-account.purview.azure.com",
    access_token=token
)

# Search for assets
results = client.search_assets(
    keywords="sales",
    entity_type="azure_sql_table"
)
```

## Examples

### Data Map Examples
- [01_search_assets.py](examples/data-map/01_search_assets.py) - Search for data assets
- [02_manage_classifications.py](examples/data-map/02_manage_classifications.py) - Add/remove classifications
- [03_manage_labels.py](examples/data-map/03_manage_labels.py) - Apply sensitivity labels
- [04_business_metadata.py](examples/data-map/04_business_metadata.py) - Set business metadata
- [05_glossary_terms.py](examples/data-map/05_glossary_terms.py) - Manage glossary terms

### Data Quality Examples
- [01_create_rules.py](examples/data-quality/01_create_rules.py) - Create quality rules
- [02_profile_assets.py](examples/data-quality/02_profile_assets.py) - Trigger profiling jobs
- [03_monitor_quality.py](examples/data-quality/03_monitor_quality.py) - Monitor quality status

### Workflow Examples
- [01_create_workflow.py](examples/workflow/01_create_workflow.py) - Create approval workflows
- [02_approval_flow.py](examples/workflow/02_approval_flow.py) - Handle approval requests
- [03_manage_tasks.py](examples/workflow/03_manage_tasks.py) - Task management

### Advanced Examples
- [01_bulk_operations.py](examples/advanced/01_bulk_operations.py) - Bulk entity updates
- [02_pagination.py](examples/advanced/02_pagination.py) - Handle paginated results
- [03_error_handling.py](examples/advanced/03_error_handling.py) - Robust error handling

## Key Features

### 🔐 Authentication
- Service principal (client credentials) flow
- Automatic token refresh
- Shared token across multiple clients

### 🔄 Retry Logic
- Exponential backoff for rate limiting (429)
- Automatic retry for transient errors (5xx)
- Configurable retry attempts

### 📝 Comprehensive Documentation
- Links to official Microsoft documentation
- Real-world examples with expected output
- Troubleshooting guides for common issues

### 🧪 Known API Limitations
- Documented workarounds for API bugs
- Alternative approaches when endpoints fail
- Community-tested solutions

## RBAC Requirements

Different API operations require specific Purview roles:

| API Surface | Required Role | Assignment Location |
|-------------|---------------|---------------------|
| Data Map (read) | Data Reader | Data Map → Collections → Role assignments |
| Data Map (write) | Data Curator | Data Map → Collections → Role assignments |
| Glossary | Data Curator | Data Map → Collections → Role assignments |
| Data Sources | Data Source Administrator | Data Map → Collections → Role assignments |
| Data Quality | Data Quality Steward | Unified Catalog → Governance Domains → Role assignments |
| Workflow | Workflow Admin | Purview Portal → Management → Role assignments |

See [Getting Started Guide](docs/getting-started.md) for detailed RBAC setup instructions.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Ways to contribute:
- 🐛 Report bugs or API issues
- 📝 Improve documentation
- 💡 Share workarounds for API limitations
- ✨ Add new examples
- 🔧 Enhance client implementations

## Community & Support

- **Issues**: [GitHub Issues](https://github.com/ahmedashraffcih/purview-api-guide/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ahmedashraffcih/purview-api-guide/discussions)
- **Official Microsoft Docs**: [Microsoft Learn - Purview](https://learn.microsoft.com/en-us/purview/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial, community-maintained resource. Microsoft Purview, Azure, and related trademarks are property of Microsoft Corporation. This project is not affiliated with or endorsed by Microsoft.

For official support and documentation, please visit:
- [Microsoft Purview Documentation](https://learn.microsoft.com/en-us/purview/)
- [Azure Support](https://azure.microsoft.com/en-us/support/)

## Acknowledgments

Built by the community, for the community. Special thanks to all contributors who have shared their knowledge and code.

---

If you find this guide helpful, please ⭐ star the repository and share it with others working with Purview APIs.
