# API Limitations and Workarounds

This document catalogs known issues, limitations, and workarounds when working with Microsoft Purview REST APIs. These are based on community testing and real-world usage.

> 💡 **Contribute**: Found a new issue or workaround? Please [open an issue](https://github.com/yourusername/purview-api-guide/issues) or submit a PR!

## Data Map / Atlas API

### 1. Basic Search Endpoint Returns 400

**Issue**: The basic search endpoint fails in some environments:

```http
GET /datamap/api/atlas/v2/search/basic?query=*&limit=10
Response: 400 Bad Request
```

**Workaround**: Use the Search Query endpoint instead:

```http
POST /datamap/api/search/query?api-version=2023-09-01
Content-Type: application/json

{
  "keywords": "*",
  "limit": 10,
  "filter": {
    "entityType": "azure_sql_table"
  }
}
```

**Status**: Documented workaround, no official fix timeline

**Code Example**:
```python
# ❌ Don't use
# results = client.get("/datamap/api/atlas/v2/search/basic", params={"query": "*"})

# ✅ Use instead
results = client.search_query(keywords="*", entity_type="azure_sql_table")
```

**References**:
- Client implementation: `clients/datamap_client.py:search_assets()`

---

### 2. Partial Entity Update Endpoint Returns 404

**Issue**: The partial attribute update endpoint is not available:

```http
PUT /datamap/api/atlas/v2/entity/guid/{guid}/partial?api-version=2023-09-01
Response: 404 Not Found
```

**Workaround**: Use the full entity create/update endpoint instead:

1. GET the full entity
2. Modify the desired attributes
3. PUT the complete entity back

```python
# Get full entity
entity = client.get_entity(guid)

# Modify attribute
entity["entity"]["attributes"]["description"] = "New description"

# Update full entity (use catalog endpoint, not datamap)
response = client.put(
    f"/catalog/api/atlas/v2/entity?api-version=2023-09-01",
    json={"entity": entity["entity"]}
)
```

**Caveat**: Changes to `lastModifiedTS` and `updatedBy` even for attribute-only updates.

**Status**: Documented workaround

**Code Example**: See `clients/datamap_client.py:set_description()`

---

### 3. Business Metadata Type Applicability Restrictions

**Issue**: Business metadata types must be explicitly configured as applicable to specific entity types. Attempting to attach a business metadata type to an incompatible entity returns:

```
ATLAS-404-00-007: Given typename <business-metadata-type> is not applicable for entity type <entity-type>
```

**Example**: A business metadata type configured for `azure_sql_table` cannot be attached to `databricks_table` entities.

**Workaround**:
1. Check business metadata type definition: `GET /datamap/api/atlas/v2/types/typedef/name/{type-name}`
2. Verify `applicableEntityTypes` array includes your target entity type
3. If not applicable, create a new business metadata type or modify the existing one

**Prevention**: When creating business metadata types, set `applicableEntityTypes: ["DataSet"]` to make them universally applicable to all dataset types.

**Code Example**:
```python
# Check applicability first
bm_type = client.get(f"/datamap/api/atlas/v2/types/typedef/name/MyBusinessMetadata")
applicable_types = bm_type.get("businessMetadataDefs", [{}])[0].get("applicableEntityTypes", [])

if entity_type not in applicable_types:
    print(f"⚠️ Business metadata not applicable to {entity_type}")
    print(f"Applicable types: {applicable_types}")
```

---

### 4. Classification Duplication Errors

**Issue**: Adding a classification that already exists on an entity returns an error:

```
Classification <classification-name> is already associated with entity <guid>
```

**Workaround**: Check existing classifications before adding:

```python
def add_classification_safe(client, guid, classification_name):
    """Add classification only if not already present."""
    entity = client.get_entity(guid)
    existing = [c["typeName"] for c in entity.get("entity", {}).get("classifications", [])]

    if classification_name not in existing:
        client.add_classifications(guid, [classification_name])
        print(f"✅ Added classification: {classification_name}")
    else:
        print(f"ℹ️ Classification already exists: {classification_name}")
```

**Code Example**: See `examples/data-map/02_manage_classifications.py`

---

### 5. Search API Does Not Support -uall Flag

**Issue**: Using `git status -uall` equivalent flags in search queries can cause memory issues on large catalogs.

**Workaround**: Avoid broad wildcard searches. Use specific filters:

```python
# ❌ Avoid
results = client.search_assets(keywords="*", limit=10000)

# ✅ Better
results = client.search_assets(
    keywords="sales",
    entity_type="azure_sql_table",
    limit=100
)
```

---

## Data Quality API

### 6. Data Quality Rules Missing 'columns' Array

**Issue**: Quality rules created via API fail during scan execution with error:

```
DQ-MissingColumn: Rule validation failed - missing column metadata
```

This occurs when the rule body doesn't include a `columns` array in `typeProperties`, even though the Purview Portal UI adds this automatically.

**Incorrect rule body**:
```json
{
  "name": "Check Nulls",
  "type": "CustomSQL",
  "typeProperties": {
    "condition": "SELECT COUNT(*) FROM {table} WHERE participant_id IS NULL"
  }
}
```

**Correct rule body**:
```json
{
  "name": "Check Nulls",
  "type": "CustomSQL",
  "typeProperties": {
    "condition": "SELECT COUNT(*) FROM {table} WHERE participant_id IS NULL",
    "columns": [
      {"value": "participant_id", "type": "Column"}
    ]
  }
}
```

**Workaround**: Always include `columns` array. Extract column names from SQL:

```python
import re

def extract_columns_from_sql(sql):
    """Extract column names from SQL WHERE clauses."""
    # Simple regex - enhance for complex queries
    pattern = r'\b(\w+)\s+IS\s+NULL'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return [{"value": col, "type": "Column"} for col in matches]

sql = "SELECT COUNT(*) FROM {table} WHERE participant_id IS NULL"
columns = extract_columns_from_sql(sql)  # [{"value": "participant_id", "type": "Column"}]
```

**Best Practice**: Validate column names against asset schema before creating rules. See `notebooks/12_create_rules_from_catalog.ipynb` for schema validation implementation.

**Status**: Workaround required

**Code Example**: See `examples/data-quality/01_create_rules.py`

---

### 7. Profiling Statistics Not Retrievable via REST API

**Issue**: The Data Quality REST API can trigger profiling jobs and monitor their status, but **cannot retrieve profiling statistics** (row counts, column distributions, null counts, etc.).

**What works**:
```python
# ✅ Trigger profiling
response = client.post(f"/datagov/quality/data-assets/{asset_id}:profile")
run_id = response["result"]["value"]

# ✅ Monitor job status
status = client.get(f"/datagov/quality/business-domains/{domain_id}/runs/{run_id}")
print(status["status"])  # "Succeeded", "Failed", "InProgress", etc.

# ✅ List run history
runs = client.get(f"/datagov/quality/data-assets/{asset_id}/runs?runType=Profile")
```

**What does NOT work**:
```python
# ❌ No endpoint exists to retrieve profiling statistics
stats = client.get(f"/datagov/quality/data-assets/{asset_id}/profile-results")
# Response: 404 Not Found
```

**Workaround**: View profiling statistics in the Purview Portal UI:
1. Navigate to **Unified Catalog** → **Data Products** → Select product
2. Click **Data Assets** → Select asset
3. Go to **Quality** tab → **Profile** subtab

**Alternative**: Use PowerShell or other Microsoft Graph APIs (if available) to extract profile data.

**Status**: API limitation - no known REST API workaround

---

### 8. Profiling Job "DQ-DSL-BuildError" Errors

**Issue**: Profiling jobs fail with:

```
DQ-DSL-BuildError: Unable to build job DSL - configuration mismatch
```

**Common Causes**:
1. **Wrong data source type** in profile body
2. **Invalid dataSourceId** (not registered with business domain)
3. **Missing schema information**

**Workaround**:

**Step 1**: Use Observer endpoint to check asset metadata:
```python
response = client.get(f"/datagov/quality/data-assets/{asset_id}/asset-metadata")
print(f"Data source type: {response['type']}")
print(f"Schema: {response['schema']}")
```

**Step 2**: Ensure profile body `type` matches data source:
```python
profile_body = {
    "type": "AzureSqlDatabase",  # Must match actual data source type
    "dataSourceId": "<valid-connection-id>",
    "tables": [...]
}
```

**Step 3**: Verify data source is registered with the business domain:
```python
# List data sources
sources = client.get(f"/datagov/quality/business-domains/{domain_id}/data-sources")
valid_source_ids = [s["id"] for s in sources["value"]]

if data_source_id not in valid_source_ids:
    print("⚠️ Data source not registered with this domain")
```

**Status**: Configuration issue, not API bug

---

### 9. Profiling Job Status "Skipped"

**Issue**: Profiling job completes with status `Skipped` instead of `Succeeded`.

**Cause**: Data has not changed since last successful profile run. Purview optimizes by skipping redundant profiling.

**Resolution**: This is expected behavior. Previous profiling results remain valid and visible in the Portal.

**To force re-profiling**: Modify the asset (e.g., update description) to invalidate the cache.

---

### 10. Profiling Run ID Field Name Confusion

**Issue**: API responses use inconsistent field names for run IDs:

```python
# Trigger profile response
response = client.post(f".../{asset_id}:profile")
run_id = response["result"]["value"]  # NOT response["id"] or response["operationId"]

# Run history response
runs = client.get(f".../runs?runType=Profile")
for run in runs["value"]:
    run_id = run["runId"]  # NOT run["id"]
```

**Workaround**: Always check the correct field name in API responses. Don't assume consistent naming.

**Status**: API design inconsistency

---

## Workflow API

### 11. Workflow Status Polling Required

**Issue**: Workflow submission returns immediately, but task creation is asynchronous. Polling is required to detect tasks.

**Workaround**:
```python
import time

# Submit workflow request
request_id = client.submit_user_request(workflow_id, payload)

# Poll for tasks (with timeout)
timeout = 60  # seconds
start = time.time()

while time.time() - start < timeout:
    tasks = client.list_tasks(workflow_id)
    if tasks:
        print(f"✅ Task created: {tasks[0]['id']}")
        break
    time.sleep(2)
else:
    print("⚠️ Task not created within timeout")
```

**Status**: Expected behavior

---

## General API Limitations

### 12. Rate Limiting (429 Errors)

**Issue**: Purview APIs enforce rate limits. Exceeding limits returns:

```
HTTP 429 Too Many Requests
Retry-After: 60
```

**Mitigation**: Clients automatically implement exponential backoff retry logic.

**Best Practices**:
- Batch operations when possible
- Add delays between bulk operations
- Respect `Retry-After` header

**Code Example**: See `clients/base_client.py:_request_with_retry()`

---

### 13. Token Expiration

**Issue**: Access tokens expire after ~60 minutes. Long-running scripts may encounter 401 errors mid-execution.

**Workaround**: Clients automatically refresh tokens. For custom implementations:

```python
from clients.auth import get_access_token

class TokenManager:
    def __init__(self):
        self.token = None
        self.expires_at = 0

    def get_token(self):
        import time
        if time.time() >= self.expires_at - 300:  # Refresh 5 min early
            self.token = get_access_token()
            self.expires_at = time.time() + 3600
        return self.token
```

---

### 14. API Version Changes

**Issue**: API endpoints may behave differently across versions. Some features are only available in preview versions.

**Example**: Data Quality API `2025-09-01-preview` has different profiling endpoints than `2024-05-01`.

**Best Practice**:
- Pin API versions in production code
- Test thoroughly when upgrading API versions
- Check official release notes for breaking changes

---

## How to Report New Issues

Found a new API limitation? Help the community:

1. **Verify it's reproducible**: Test with different accounts/tenants
2. **Check official docs**: Ensure it's not expected behavior
3. **Document workaround**: If you found a solution, share it!
4. **Open an issue**: [GitHub Issues](https://github.com/yourusername/purview-api-guide/issues)

Include:
- API endpoint and method
- Request/response examples
- Error messages
- Purview account type (if relevant)
- API version used

---

## Official Channels for Microsoft Support

For official support with Purview APIs:

- **Azure Support**: Submit a support ticket via Azure Portal
- **Microsoft Learn Q&A**: [Purview Q&A](https://learn.microsoft.com/en-us/answers/tags/134/azure-purview)
- **GitHub Issues** (for SDK bugs): [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python/issues)

---

**Last Updated**: 2026-02-03

**Contributions**: This document is community-maintained. Submit PRs with new findings!
