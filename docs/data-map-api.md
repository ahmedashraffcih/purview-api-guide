# Data Map API Guide

The Data Map API (also known as Atlas API) provides access to Purview's core metadata catalog. Use it to search for data assets, manage classifications, apply labels, set business metadata, and work with glossary terms.

## Official Documentation

- [Data Map API Reference](https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane)
- [Atlas API Concepts](https://learn.microsoft.com/en-us/purview/concept-elastic-data-map)

## Authentication & Authorization

**Endpoint**: `https://<your-account>.purview.azure.com/datamap/api/`

**Required Roles**:
- **Data Reader**: Search and view entities
- **Data Curator**: Modify entities, manage classifications, glossary terms
- **Data Source Administrator**: Register and manage data sources

Assign roles at: **Purview Portal** → **Data Map** → **Collections** → **Role assignments**

## Client Setup

```python
from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token
import os

# Authenticate
token = get_access_token()

# Create client
client = PurviewDataMapClient(
    endpoint=os.getenv("PURVIEW_ENDPOINT"),
    access_token=token,
    api_version="2023-09-01"  # Default
)
```

## Common Operations

### 1. Search for Assets

Search the catalog for data assets by keywords, entity type, or filters.

```python
# Search for all SQL tables
results = client.search_assets(
    keywords="customer",
    entity_type="azure_sql_table",
    limit=50
)

for asset in results:
    print(f"{asset['name']} - {asset['qualifiedName']}")
```

**Entity Types**:
- `azure_sql_table` - Azure SQL Database tables
- `databricks_table` - Databricks tables
- `adls_gen2_filesystem` - Azure Data Lake Gen2 filesystems
- `azure_blob_container` - Azure Blob containers
- `azure_sql_db` - Azure SQL Database
- `azure_synapse_dedicated_sql_pool` - Synapse dedicated SQL pools

**Important**: The basic search endpoint (`GET /datamap/api/atlas/v2/search/basic`) returns 400 in some environments. The client uses the search query endpoint (`POST /datamap/api/search/query`) instead. See [API Limitations](api-limitations.md).

### 2. Get Entity Details

Retrieve full entity metadata including attributes, classifications, and relationships.

```python
# Get entity by GUID
entity = client.get_entity(guid="entity-guid-here")

# Access attributes
attrs = entity["entity"]["attributes"]
print(f"Name: {attrs['name']}")
print(f"Description: {attrs.get('description', 'N/A')}")
print(f"Owner: {attrs.get('owner', 'N/A')}")

# Access classifications
classifications = entity["entity"].get("classifications", [])
for cls in classifications:
    print(f"Classification: {cls['typeName']}")

# Access related entities (e.g., columns for tables)
referred_entities = entity.get("referredEntities", {})
```

### 3. Update Entity Description

Update entity attributes like description, owner, or custom properties.

```python
# Update description
client.set_description(
    guid="entity-guid",
    description="Customer master data table containing PII"
)
```

**Note**: The partial update endpoint (`PUT /entity/guid/{guid}/partial`) is not available. The client uses the full entity update approach. See [API Limitations](api-limitations.md).

### 4. Add Classifications

Apply sensitivity or data classifications to assets.

```python
# Add single classification
client.add_classifications(
    guid="entity-guid",
    classifications=["MICROSOFT.PERSONAL.NAME"]
)

# Add classification with attributes
client.add_classifications(
    guid="entity-guid",
    classifications=[
        {
            "typeName": "MICROSOFT.FINANCIAL.CREDIT_CARD",
            "attributes": {}
        }
    ]
)
```

**Common Classifications**:
- `MICROSOFT.PERSONAL.NAME`
- `MICROSOFT.PERSONAL.EMAIL`
- `MICROSOFT.PERSONAL.PHONE_NUMBER`
- `MICROSOFT.PERSONAL.SSN`
- `MICROSOFT.FINANCIAL.CREDIT_CARD`
- `MICROSOFT.GOVERNMENT.US.PASSPORT_NUMBER`

**Important**: Check existing classifications before adding to avoid "already associated" errors. See [API Limitations](api-limitations.md).

### 5. Apply Sensitivity Labels

Apply Microsoft Purview sensitivity labels to assets.

```python
# Apply label
client.add_labels(
    guid="entity-guid",
    labels=["Highly Confidential"]
)

# Remove labels
client.set_labels(
    guid="entity-guid",
    labels=[]  # Empty list removes all labels
)
```

**Typical Labels**:
- `Public`
- `General`
- `Confidential`
- `Highly Confidential`

Labels must be defined in Microsoft Purview Information Protection settings.

### 6. Set Business Metadata

Apply custom business metadata to entities for governance tracking.

```python
# Set business metadata
client.set_business_metadata(
    guid="entity-guid",
    business_metadata={
        "DQ_Enrichment": {
            "Status": "Validated",
            "LastReviewDate": "2024-01-15",
            "DataSteward": "john.doe@company.com"
        }
    }
)
```

**Important**: Business metadata types must be pre-configured and applicable to the entity type. See [API Limitations](api-limitations.md).

### 7. Set Contacts

Assign owners and experts to data assets.

```python
# Set contacts
client.set_contacts(
    guid="entity-guid",
    owners=["john.doe@company.com"],
    experts=["jane.smith@company.com"]
)
```

Contacts must be valid user principal names (UPNs) in your Azure AD tenant.

### 8. Glossary Term Management

Create and assign glossary terms to standardize business vocabulary.

```python
# Create glossary term
term = client.create_glossary_term(
    glossary_guid="glossary-guid",
    term_name="Customer Churn Rate",
    term_description="Percentage of customers who cancel service in a given period",
    parent_term_guid=None  # Optional: for hierarchical terms
)

# Assign term to entity
client.assign_term_to_entity(
    term_guid=term["guid"],
    entity_guids=["entity-guid-1", "entity-guid-2"]
)

# Get term details
term = client.get_glossary_term(term_guid="term-guid")
```

**Glossary Term Structure**:
```python
{
    "name": "Term Name",
    "description": "Definition of the term",
    "status": "Draft",  # Draft, Approved, Alert
    "abbreviation": "TN",
    "synonyms": ["Synonym1", "Synonym2"],
    "relatedTerms": [],
    "parentTerm": {"termGuid": "parent-guid"}
}
```

## Entity Relationships

Navigate relationships between entities (e.g., table → columns, database → tables).

```python
# Get entity with referred entities
entity = client.get_entity(guid="table-guid")

# Access columns
referred_entities = entity.get("referredEntities", {})
relationship_attrs = entity["entity"].get("relationshipAttributes", {})
column_guids = [rel["guid"] for rel in relationship_attrs.get("columns", [])]

# Get column details
for col_guid in column_guids:
    if col_guid in referred_entities:
        column = referred_entities[col_guid]
        print(f"Column: {column['attributes']['name']}")
        print(f"  Type: {column['attributes']['dataType']}")
```

## Bulk Operations

Process multiple entities efficiently with error handling.

```python
from examples.advanced.bulk_operations import bulk_add_labels

# Add labels to multiple assets
results = bulk_add_labels(
    client=client,
    asset_guids=["guid1", "guid2", "guid3"],
    labels=["Confidential"]
)

print(f"Success: {results['success']}, Failed: {results['failed']}")
```

See [examples/advanced/01_bulk_operations.py](../examples/advanced/01_bulk_operations.py) for complete implementation.

## API Versions

The Data Map API has evolved across versions:

- **2023-09-01** (Recommended): Latest stable version with full feature support
- **2022-03-01-preview**: Preview features, may change
- **2021-07-01**: Older version, missing newer features

Specify version when creating the client:

```python
client = PurviewDataMapClient(
    endpoint=endpoint,
    access_token=token,
    api_version="2023-09-01"
)
```

## Common Patterns

### Find Entity by Qualified Name

```python
# Search for entity by qualified name
results = client.search_assets(
    keywords=qualified_name,
    limit=1
)

if results:
    entity_guid = results[0]["id"]
    entity = client.get_entity(entity_guid)
```

### Batch Update Descriptions from CSV

```python
import csv

with open('descriptions.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            client.set_description(
                guid=row['entity_guid'],
                description=row['description']
            )
            print(f"✅ Updated {row['entity_guid']}")
        except Exception as e:
            print(f"❌ Failed {row['entity_guid']}: {e}")
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Missing RBAC role | Assign Data Curator role |
| 404 Not Found | Invalid GUID or entity deleted | Verify GUID, search for entity first |
| 400 Bad Request | Invalid payload or parameters | Check API documentation for correct format |
| ATLAS-404-00-007 | Business metadata type not applicable | Verify type is configured for entity type |
| "Already associated" | Classification already exists | Check existing classifications first |

See [Troubleshooting Guide](troubleshooting.md) for detailed error solutions.

## Known Limitations

1. **Basic search endpoint returns 400** - Use search query endpoint instead
2. **Partial update endpoint not available** - Use full entity update
3. **Business metadata type restrictions** - Types must be pre-configured as applicable
4. **Classification deduplication required** - Check before adding

See [API Limitations](api-limitations.md) for complete list and workarounds.

## Examples

Complete working examples:

- [01_search_assets.py](../examples/data-map/01_search_assets.py) - Search and discover assets
- [02_manage_classifications.py](../examples/data-map/02_manage_classifications.py) - Apply classifications
- [03_manage_labels.py](../examples/data-map/03_manage_labels.py) - Manage sensitivity labels
- [04_business_metadata.py](../examples/data-map/04_business_metadata.py) - Set business metadata
- [05_glossary_terms.py](../examples/data-map/05_glossary_terms.py) - Manage glossary

## Next Steps

- [Data Quality API Guide](data-quality-api.md) - Quality rules and profiling
- [Workflow API Guide](workflow-api.md) - Approval workflows
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
