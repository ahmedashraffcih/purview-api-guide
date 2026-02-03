# Data Quality API Guide

The Data Quality API (part of Data Governance APIs) enables you to create quality rules, trigger profiling jobs, and monitor data quality assessments programmatically.

## Official Documentation

- [Data Quality API Reference](https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane)
- [Data Quality Concepts](https://learn.microsoft.com/en-us/purview/concept-data-quality)

## Authentication & Authorization

**Endpoint**: `https://api.purview-service.microsoft.com/datagov/quality/`

**Important**: Data Quality APIs use a different endpoint than Data Map APIs, but the same authentication token.

**Required Roles**:
- **Data Quality Steward**: Create/manage rules, trigger profiling, run assessments
- **Data Quality Viewer**: View quality results (read-only)

Assign roles at: **Purview Portal** → **Unified Catalog** → **Catalog Management** → **Governance Domains** → **Role assignments**

## Client Setup

```python
from clients.dataquality_client import PurviewDataQualityClient
from clients.auth import get_access_token

# Authenticate (same token for all Purview APIs)
token = get_access_token()

# Create client
client = PurviewDataQualityClient(
    access_token=token,
    endpoint="https://api.purview-service.microsoft.com",  # Default
    api_version="2025-09-01-preview"  # Default
)
```

## Core Concepts

### Business Domains
Governance boundaries for organizing data products and quality rules.

### Data Products
Collections of related data assets within a business domain.

### Data Assets
Individual data sources (tables, files, etc.) that have quality rules applied.

### Quality Rules
SQL-based validations that check data quality (nulls, duplicates, ranges, etc.).

### Profiling
Automated data profiling to generate statistics (row counts, distributions, etc.).

## Common Operations

### 1. List Business Domains

```python
# Get all domains
domains = client.list_domains()

for domain in domains:
    print(f"Domain: {domain['name']}")
    print(f"  ID: {domain['id']}")
    print(f"  Description: {domain.get('description', 'N/A')}")
```

### 2. List Data Products

```python
# Get data products in a domain
products = client.list_data_products(domain_id="domain-guid")

for product in products:
    print(f"Product: {product['name']}")
    print(f"  ID: {product['id']}")
```

### 3. List Data Assets

```python
# Get data assets in a data product
assets = client.list_data_assets(
    domain_id="domain-guid",
    product_id="product-guid"
)

for asset in assets:
    print(f"Asset: {asset['name']}")
    print(f"  Type: {asset['assetType']}")
    print(f"  ID: {asset['id']}")
```

### 4. Create Quality Rules

Create SQL-based quality rules to validate data.

```python
# Create a NULL check rule
rule = client.create_rule(
    business_domain_id="domain-guid",
    data_product_id="product-guid",
    data_asset_id="asset-guid",
    rule_id="check_nulls_customer_id",
    rule_body={
        "name": "Check Nulls - Customer ID",
        "description": "Ensure customer_id has no NULL values",
        "type": "CustomSQL",
        "typeProperties": {
            "condition": "SELECT COUNT(*) FROM {table} WHERE customer_id IS NULL",
            "columns": [
                {"value": "customer_id", "type": "Column"}
            ]
        },
        "severity": "High"
    }
)

print(f"Rule created: {rule['id']}")
```

**CRITICAL**: Rules must include a `columns` array in `typeProperties` to avoid "DQ-MissingColumn" errors during scans. The Purview Portal adds this automatically, but the API requires it explicitly. See [API Limitations](api-limitations.md).

**Rule Types**:
- `CustomSQL` - Custom SQL validation query
- `Freshness` - Check data freshness
- `Completeness` - Check for NULL values
- `Uniqueness` - Check for duplicates
- `Validity` - Check value ranges/formats

**Severity Levels**: `High`, `Medium`, `Low`

### 5. Common Rule Patterns

#### NULL Check Rule
```python
rule_body = {
    "name": "Check Nulls - Column Name",
    "type": "CustomSQL",
    "typeProperties": {
        "condition": "SELECT COUNT(*) FROM {table} WHERE column_name IS NULL",
        "columns": [{"value": "column_name", "type": "Column"}]
    },
    "severity": "High"
}
```

#### Duplicate Check Rule
```python
rule_body = {
    "name": "Check Duplicates - Primary Key",
    "type": "CustomSQL",
    "typeProperties": {
        "condition": "SELECT id, COUNT(*) FROM {table} GROUP BY id HAVING COUNT(*) > 1",
        "columns": [{"value": "id", "type": "Column"}]
    },
    "severity": "High"
}
```

#### Value Range Rule
```python
rule_body = {
    "name": "Check Age Range",
    "type": "CustomSQL",
    "typeProperties": {
        "condition": "SELECT COUNT(*) FROM {table} WHERE age < 0 OR age > 120",
        "columns": [{"value": "age", "type": "Column"}]
    },
    "severity": "Medium"
}
```

### 6. List Rules for an Asset

```python
# Get all rules for a data asset
rules = client.list_rules(
    business_domain_id="domain-guid",
    data_product_id="product-guid",
    data_asset_id="asset-guid"
)

for rule in rules:
    print(f"Rule: {rule['name']}")
    print(f"  Type: {rule['type']}")
    print(f"  Severity: {rule['severity']}")
```

### 7. Update or Delete Rules

```python
# Update rule (PUT with updated body)
updated_rule = client.create_rule(  # Same method, PUT is idempotent
    business_domain_id="domain-guid",
    data_product_id="product-guid",
    data_asset_id="asset-guid",
    rule_id="existing-rule-id",
    rule_body={
        # Updated rule configuration
    }
)

# Delete rule
client.delete_rule(
    business_domain_id="domain-guid",
    data_product_id="product-guid",
    data_asset_id="asset-guid",
    rule_id="rule-id"
)
```

### 8. Trigger Profiling Job

Start a profiling job to generate data statistics.

```python
# Trigger profiling for Azure SQL table
run_id = client.profile_asset(
    business_domain_id="domain-guid",
    data_product_id="product-guid",
    data_asset_id="asset-guid",
    profile_config={
        "type": "AzureSqlDatabase",
        "dataSourceId": "connection-guid",
        "tables": [
            {
                "schema": "dbo",
                "table": "customers"
            }
        ]
    }
)

print(f"Profiling job started: {run_id}")
```

**Profile Configuration by Source Type**:

#### Azure SQL Database / Synapse
```python
{
    "type": "AzureSqlDatabase",  # or "AzureSynapseAnalytics"
    "dataSourceId": "connection-guid",
    "tables": [
        {"schema": "dbo", "table": "table_name"}
    ]
}
```

#### Databricks (Delta)
```python
{
    "type": "Delta",
    "dataSourceId": "connection-guid",
    "tables": [
        {
            "catalog": "catalog_name",
            "schema": "schema_name",
            "table": "table_name"
        }
    ]
}
```

**CRITICAL**: The REST API can trigger and monitor profiling jobs but **CANNOT retrieve profiling statistics**. View profiling results in the Purview Portal UI. See [API Limitations](api-limitations.md).

### 9. Monitor Job Status

Check the status of profiling or quality assessment runs.

```python
# Get run status
status = client.get_run_status(
    business_domain_id="domain-guid",
    run_id="run-guid"
)

print(f"Status: {status['status']}")
print(f"Started: {status['submissionTime']}")
print(f"Ended: {status.get('endTime', 'Still running')}")

if status['status'] == 'Failed':
    print(f"Error: {status.get('message')}")
```

**Job Statuses**:
- `Queued` - Job is queued
- `InProgress` - Job is running
- `Succeeded` - Job completed successfully
- `Failed` - Job failed (check `message` field)
- `Skipped` - Data unchanged since last run

### 10. List Run History

Get history of quality scans and profiling jobs.

```python
# Get all runs for an asset
runs = client.list_runs(
    data_asset_id="asset-guid",
    run_type="Quality"  # "Quality" for rule scans, "Profile" for profiling
)

# Sort by submission time
sorted_runs = sorted(runs, key=lambda r: r['submissionTime'], reverse=True)

for run in sorted_runs[:10]:  # Last 10 runs
    print(f"Run: {run['runId']}")
    print(f"  Status: {run['status']}")
    print(f"  Started: {run['submissionTime']}")
```

**Important Field Names**:
- Extract run ID from `response.result.value` (NOT `response.id`) when triggering profiling
- Use `runId` field (NOT `id`) in run history responses
- Sort runs by `submissionTime` (API doesn't guarantee order)

## Data Source Connection IDs

To trigger profiling, you need the data source connection GUID. Get it from:

1. **Purview Portal**: Data Map → Data Sources → [Source] → Properties
2. **API**: Use Data Map APIs to list registered data sources

```python
# Example: Get data source connection ID (using Data Map API)
from clients.datamap_client import PurviewDataMapClient

datamap_client = PurviewDataMapClient(endpoint=purview_endpoint, access_token=token)
# Use datamap_client to list data sources and get connection IDs
```

## Catalog Asset ID vs Data Map GUID

**Important Distinction**:
- **Data Map GUID**: Entity GUID from Data Map/Atlas APIs (search results)
- **Catalog Asset ID**: Different ID used by Data Quality APIs

The Data Quality API requires the **Catalog Asset ID**, not the Data Map GUID. Get it from:
- Data Quality API's `list_data_assets()` method
- Purview Portal: Unified Catalog → Data Products → [Product] → Data Assets

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Missing Data Quality Steward role | Assign role in Unified Catalog governance domain |
| DQ-MissingColumn | Rule missing `columns` array | Add columns array to typeProperties |
| DQ-DSL-BuildError | Profile config doesn't match source type | Verify type field matches data source type |
| Asset not found | Wrong asset ID (using Data Map GUID instead of Catalog Asset ID) | Use Catalog Asset ID from list_data_assets() |
| Connection error | Invalid data source connection ID | Verify connection ID from Data Map |

See [Troubleshooting Guide](troubleshooting.md) for detailed error solutions.

## Known Limitations

1. **Profiling statistics not retrievable via API** - Must view in Portal UI
2. **Rules must include columns array** - Not auto-added like in Portal
3. **Different asset ID format** - Use Catalog Asset ID, not Data Map GUID
4. **Profile config must match source type** - Type field must be exact match

See [API Limitations](api-limitations.md) for complete list and workarounds.

## Examples

Complete working examples:

- [01_create_rules.py](../examples/data-quality/01_create_rules.py) - Create quality rules
- [02_profile_assets.py](../examples/data-quality/02_profile_assets.py) - Trigger profiling jobs
- [03_monitor_quality.py](../examples/data-quality/03_monitor_quality.py) - Monitor quality status

## Best Practices

1. **Validate columns exist** - Extract column names from SQL and verify against asset schema before creating rules
2. **Test SQL conditions** - Test SQL queries directly on data source before creating rules
3. **Use appropriate severity** - Reserve High for critical data quality issues
4. **Monitor run history** - Regularly check for failed runs
5. **Set up scheduled scans** - Configure in Portal UI for automated quality checks
6. **Document rules** - Use clear names and descriptions for maintainability

## Next Steps

- [Data Map API Guide](data-map-api.md) - Search and manage assets
- [Workflow API Guide](workflow-api.md) - Approval workflows
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
