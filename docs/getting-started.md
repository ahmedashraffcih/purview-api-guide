# Getting Started with Purview REST APIs

This guide will walk you through setting up authentication and making your first API calls to Microsoft Purview.

## Prerequisites

### 1. Azure Resources

- **Azure Subscription**: Active Azure subscription
- **Microsoft Purview Account**: Deployed Purview account (or Unified Catalog)
- **Service Principal**: Azure AD app registration for authentication

### 2. Local Environment

- **Python 3.8+**: Required for running examples
- **pip**: Python package manager
- **Git**: For cloning the repository

## Setup Steps

### Step 1: Create a Service Principal

A service principal is required for non-interactive authentication to Purview APIs.

#### Using Azure Portal

1. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
2. Enter a name (e.g., "PurviewAPIClient")
3. Select **Accounts in this organizational directory only**
4. Click **Register**
5. Note the **Application (client) ID** and **Directory (tenant) ID**
6. Go to **Certificates & secrets** → **New client secret**
7. Add description, select expiration, click **Add**
8. **Copy the secret value immediately** (it won't be shown again)

#### Using Azure CLI

```bash
# Create service principal
az ad sp create-for-rbac --name "PurviewAPIClient" --skip-assignment

# Output will contain:
# - appId (CLIENT_ID)
# - password (CLIENT_SECRET)
# - tenant (TENANT_ID)
```

### Step 2: Assign Purview RBAC Roles

Service principals need explicit Purview roles to access APIs.

#### Data Map Roles

Assign roles at: **Purview Portal** → **Data Map** → **Collections** → **Role assignments**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Collection Admin** | Full control over collection | Administrative tasks |
| **Data Source Administrator** | Manage data sources, scans | Register data sources, configure scans |
| **Data Curator** | Read/write entities, glossary | Add classifications, edit descriptions, manage glossary |
| **Data Reader** | Read-only access | Search, view entities |

**Example**: To search and update entity descriptions, assign **Data Curator** role.

#### Data Quality Roles

Assign roles at: **Purview Portal** → **Unified Catalog** → **Catalog Management** → **Governance Domains** → **Role assignments**

| Role | Permissions |
|------|-------------|
| **Data Quality Steward** | Create/manage quality rules, run assessments |
| **Data Quality Viewer** | View quality results |

#### Workflow Roles

Assign roles at: **Purview Portal** → **Management** → **Role assignments**

| Role | Permissions |
|------|-------------|
| **Workflow Admin** | Create/manage workflows |
| **Workflow Approver** | Approve/reject workflow tasks |

**⚠️ Important**: Role assignments can take 5-10 minutes to propagate. If you receive 403 errors immediately after assignment, wait and retry.

### Step 3: Install Dependencies

```bash
# Clone repository
git clone https://github.com/yourusername/purview-api-guide.git
cd purview-api-guide

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
nano .env  # or use your preferred editor
```

**.env contents:**
```bash
TENANT_ID=your-tenant-guid-here
CLIENT_ID=your-client-guid-here
CLIENT_SECRET=your-client-secret-here
PURVIEW_ENDPOINT=https://your-account-name.purview.azure.com
```

**Finding your Purview endpoint:**
- Azure Portal → Your Purview account → **Overview** → **Purview Account endpoint**
- Format: `https://<account-name>.purview.azure.com`

### Step 5: Verify Authentication

Test your credentials with a simple script:

```python
from clients.auth import get_access_token

try:
    token = get_access_token()
    print("✅ Authentication successful!")
    print(f"Token length: {len(token)} characters")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
```

## Your First API Call

### Example 1: Search for Assets

```python
from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token
import os

# Get credentials from environment
endpoint = os.getenv("PURVIEW_ENDPOINT")
token = get_access_token()

# Create client
client = PurviewDataMapClient(endpoint=endpoint, access_token=token)

# Search for assets
results = client.search_assets(
    keywords="*",  # Search for all assets
    limit=10
)

print(f"Found {len(results)} assets:")
for asset in results:
    print(f"  - {asset.get('name')} ({asset.get('typeName')})")
```

### Example 2: Get Entity Details

```python
# Get entity by qualified name
entity = client.find_entity_by_qualified_name(
    type_name="azure_sql_table",
    qualified_name="mssql://your-server.database.windows.net/your-db/dbo/your-table"
)

if entity:
    guid = entity["guid"]
    name = entity["attributes"]["name"]
    description = entity["attributes"].get("description", "No description")

    print(f"Entity: {name}")
    print(f"GUID: {guid}")
    print(f"Description: {description}")
```

## Authentication Flow

Understanding how authentication works:

```
┌─────────────────┐
│  Your Script    │
└────────┬────────┘
         │
         │ 1. Request token with credentials
         ▼
┌─────────────────────────────────┐
│  Azure AD / Entra ID            │
│  (Token Endpoint)               │
└────────┬────────────────────────┘
         │
         │ 2. Returns access token (valid ~1 hour)
         ▼
┌─────────────────┐
│  Your Script    │
└────────┬────────┘
         │
         │ 3. Call Purview API with token
         ▼
┌─────────────────────────────────┐
│  Purview API                    │
│  (Validates token + RBAC)       │
└────────┬────────────────────────┘
         │
         │ 4. Returns data
         ▼
┌─────────────────┐
│  Your Script    │
└─────────────────┘
```

### Token Scope

All Purview APIs use the same token scope:
```
https://purview.azure.net/.default
```

This single token works for:
- Data Map API (`https://<account>.purview.azure.com/datamap/...`)
- Catalog API (`https://<account>.purview.azure.com/catalog/...`)
- Scanning API (`https://<account>.purview.azure.com/scan/...`)
- Data Quality API (`https://api.purview-service.microsoft.com/...`)
- Workflow API (`https://<account>.purview.azure.com/workflow/...`)

### Token Lifetime

- **Default lifetime**: ~60 minutes
- **Automatic refresh**: Clients handle token refresh automatically
- **Best practice**: Cache tokens and reuse across requests

## Common Setup Issues

### Issue: 401 Unauthorized

**Cause**: Invalid credentials or expired token

**Solution**:
```bash
# Verify credentials
echo $TENANT_ID
echo $CLIENT_ID
echo $CLIENT_SECRET  # Should not be empty

# Test authentication
python -c "from clients.auth import get_access_token; print(get_access_token()[:50])"
```

### Issue: 403 Forbidden

**Cause**: Missing RBAC role assignment

**Solution**:
1. Verify role assignment in Purview Portal
2. Wait 5-10 minutes for propagation
3. Check you're assigned to the correct collection/domain
4. Ensure service principal (not user) has the role

### Issue: 404 Not Found

**Cause**: Incorrect endpoint URL

**Solution**:
```python
# Verify endpoint format
endpoint = os.getenv("PURVIEW_ENDPOINT")
print(f"Endpoint: {endpoint}")

# Should be: https://<account-name>.purview.azure.com
# NOT: https://<account-name>.purview.azure.com/
# NOT: https://web.purview.azure.com/...
```

### Issue: SSL Certificate Errors

**Cause**: Corporate proxy or firewall

**Solution**:
```python
# Temporarily disable SSL verification (NOT for production)
import requests
requests.packages.urllib3.disable_warnings()

# Or configure proxy
import os
os.environ['HTTPS_PROXY'] = 'http://your-proxy:port'
```

## API Versions

Different API surfaces use different versions:

| API | Current Version | Path Example |
|-----|----------------|--------------|
| Data Map | `2023-09-01` | `/datamap/api/atlas/v2/search/query?api-version=2023-09-01` |
| Catalog | `2023-09-01` | `/catalog/api/atlas/v2/entity?api-version=2023-09-01` |
| Scanning | `2023-09-01` | `/scan/datasources?api-version=2023-09-01` |
| Data Quality | `2025-09-01-preview` | `/datagov/quality/...?api-version=2025-09-01-preview` |
| Workflow | `2023-10-01-preview` | `/workflow/runs?api-version=2023-10-01-preview` |

**Note**: Clients automatically inject the correct API version.

## Next Steps

✅ **Authentication working?** Try the examples:
- [Data Map Examples](../examples/data-map/)
- [Data Quality Examples](../examples/data-quality/)
- [Workflow Examples](../examples/workflow/)

📖 **Learn more**:
- [Data Map API Guide](data-map-api.md)
- [Data Quality API Guide](data-quality-api.md)
- [API Limitations](api-limitations.md)

🔗 **Official Documentation**:
- [Purview REST API Reference](https://learn.microsoft.com/en-us/rest/api/purview/)
- [Azure AD Authentication](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)
