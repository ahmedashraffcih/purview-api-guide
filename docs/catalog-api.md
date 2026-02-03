# Catalog API Guide

The Catalog API is part of the Purview Data Map and provides entity management operations. In most cases, you'll use the Data Map client which wraps both `/datamap/api/` and `/catalog/api/` endpoints.

## Official Documentation

- [Catalog API Reference](https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane)
- [Entity Management](https://learn.microsoft.com/en-us/purview/catalog-entities)

## Endpoints

Purview has two related API surfaces:

1. **Data Map API**: `https://<account>.purview.azure.com/datamap/api/`
   - Search, discovery, type definitions

2. **Catalog API**: `https://<account>.purview.azure.com/catalog/api/`
   - Entity CRUD operations, classifications, lineage

**Important**: Use the **Data Map Client** for both - it automatically routes requests to the correct endpoint.

## Authentication & Authorization

Same as Data Map API. See [Data Map API Guide](data-map-api.md) for full details.

**Required Roles**:
- **Data Reader**: Read entities
- **Data Curator**: Create/update entities, manage classifications

## Client Setup

```python
from clients.datamap_client import PurviewDataMapClient
from clients.auth import get_access_token
import os

# The Data Map client handles both /datamap and /catalog endpoints
token = get_access_token()

client = PurviewDataMapClient(
    endpoint=os.getenv("PURVIEW_ENDPOINT"),
    access_token=token
)
```

## When to Use Catalog Endpoints

The client automatically uses Catalog endpoints for:

1. **Full entity updates** - When updating entity attributes
2. **Bulk entity operations** - Creating/updating multiple entities
3. **Entity creation** - Creating new custom entities
4. **Lineage operations** - Managing entity relationships

You typically don't need to call Catalog endpoints directly - use the Data Map client methods.

## Common Catalog Operations

### 1. Get Entity (via Catalog)

```python
# Get entity by GUID
# This uses GET /catalog/api/atlas/v2/entity/guid/{guid}
entity = client.get_entity(guid="entity-guid")

# Access entity data
attrs = entity["entity"]["attributes"]
print(f"Name: {attrs['name']}")
print(f"Type: {entity['entity']['typeName']}")
```

### 2. Update Entity

The client uses the Catalog endpoint for full entity updates:

```python
# Update entity attributes
# This uses PUT /catalog/api/atlas/v2/entity
client.set_description(
    guid="entity-guid",
    description="Updated description"
)
```

**Note**: The partial update endpoint (`PUT /datamap/api/atlas/v2/entity/guid/{guid}/partial`) is not available. The client fetches the full entity, modifies attributes, and sends a complete update via the Catalog endpoint. See [API Limitations](api-limitations.md).

### 3. Bulk Create/Update Entities

Create or update multiple entities in a single request:

```python
# Bulk entity update
entities = [
    {
        "typeName": "azure_sql_table",
        "attributes": {
            "name": "customers",
            "qualifiedName": "mssql://server.database.windows.net/db/dbo/customers",
            "description": "Customer master data"
        }
    },
    {
        "typeName": "azure_sql_table",
        "attributes": {
            "name": "orders",
            "qualifiedName": "mssql://server.database.windows.net/db/dbo/orders",
            "description": "Order transactions"
        }
    }
]

# Use POST /catalog/api/atlas/v2/entity/bulk
response = client.post(
    "/catalog/api/atlas/v2/entity/bulk",
    json={"entities": entities},
    params={"api-version": "2023-09-01"}
)

created_entities = response.json()
print(f"Created {len(created_entities['mutatedEntities']['CREATE'])} entities")
```

### 4. Delete Entity

Delete an entity by GUID:

```python
# Delete entity
# Uses DELETE /catalog/api/atlas/v2/entity/guid/{guid}
response = client.delete(
    f"/catalog/api/atlas/v2/entity/guid/{guid}",
    params={"api-version": "2023-09-01"}
)

print(f"Entity deleted: {guid}")
```

### 5. Create Custom Entity

Create a custom entity with specific type and attributes:

```python
# Create custom entity
entity = {
    "entity": {
        "typeName": "your_custom_type",
        "attributes": {
            "name": "Entity Name",
            "qualifiedName": "unique-qualified-name",
            "description": "Description",
            # Add other required attributes based on type definition
        }
    }
}

response = client.post(
    "/catalog/api/atlas/v2/entity",
    json=entity,
    params={"api-version": "2023-09-01"}
)

created_entity = response.json()
entity_guid = created_entity["guidAssignments"]["0"]
print(f"Entity created: {entity_guid}")
```

**Note**: Custom types must be defined first using Type Definition APIs.

## Entity Structure

Entities returned from Catalog API have this structure:

```json
{
    "entity": {
        "guid": "entity-guid",
        "typeName": "azure_sql_table",
        "status": "ACTIVE",
        "attributes": {
            "name": "customers",
            "qualifiedName": "mssql://...",
            "description": "Customer data",
            "owner": "john.doe@company.com",
            "createTime": 1234567890,
            "updateTime": 1234567900
        },
        "classifications": [
            {
                "typeName": "MICROSOFT.PERSONAL.NAME",
                "attributes": {}
            }
        ],
        "labels": ["Confidential"],
        "relationshipAttributes": {
            "columns": [
                {"guid": "column-guid-1"},
                {"guid": "column-guid-2"}
            ]
        }
    },
    "referredEntities": {
        "column-guid-1": {
            "guid": "column-guid-1",
            "typeName": "azure_sql_column",
            "attributes": {
                "name": "customer_id",
                "dataType": "int"
            }
        }
    }
}
```

## Type Definitions

Manage entity type definitions (custom types, classifications, business metadata):

```python
# Get all type definitions
response = client.get(
    "/catalog/api/atlas/v2/types/typedefs",
    params={"api-version": "2023-09-01"}
)

typedefs = response.json()

# Access different type categories
entity_types = typedefs["entityDefs"]
classification_types = typedefs["classificationDefs"]
business_metadata_types = typedefs["businessMetadataDefs"]
```

## Lineage Operations

Retrieve and manage entity lineage (data flow relationships):

```python
# Get entity lineage
response = client.get(
    f"/catalog/api/atlas/v2/lineage/{guid}",
    params={
        "api-version": "2023-09-01",
        "direction": "BOTH",  # BOTH, INPUT, OUTPUT
        "depth": 3
    }
)

lineage = response.json()

# Access upstream/downstream entities
upstream_relations = lineage.get("guidEntityMap", {})
```

## Relationship Management

Create and manage relationships between entities:

```python
# Create relationship
relationship = {
    "typeName": "relationship_type",
    "attributes": {},
    "end1": {
        "guid": "entity-guid-1",
        "typeName": "entity-type-1"
    },
    "end2": {
        "guid": "entity-guid-2",
        "typeName": "entity-type-2"
    }
}

response = client.post(
    "/catalog/api/atlas/v2/relationship",
    json=relationship,
    params={"api-version": "2023-09-01"}
)
```

## Data Map vs Catalog Endpoint Routing

The `PurviewDataMapClient` handles endpoint routing automatically:

| Operation | Client Method | Actual Endpoint |
|-----------|---------------|-----------------|
| Search assets | `search_assets()` | `POST /datamap/api/search/query` |
| Get entity | `get_entity()` | `GET /catalog/api/atlas/v2/entity/guid/{guid}` |
| Update entity | `set_description()` | `PUT /catalog/api/atlas/v2/entity` |
| Add labels | `add_labels()` | `POST /catalog/api/atlas/v2/entity/guid/{guid}/labels` |
| Add classifications | `add_classifications()` | `POST /catalog/api/atlas/v2/entity/guid/{guid}/classifications` |

## Error Handling

Common Catalog API errors:

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Missing Data Curator role | Assign role in Data Map collections |
| 404 Not Found | Invalid GUID | Verify entity exists via search first |
| 400 Bad Request | Invalid entity structure | Check required attributes for entity type |
| ATLAS-400-00-05C | Invalid qualified name format | Use correct format for entity type |
| ATLAS-400-00-078 | Entity already exists | Use update instead of create |

See [Troubleshooting Guide](troubleshooting.md) for detailed solutions.

## API Version

Use the same API version as Data Map API:

```python
client = PurviewDataMapClient(
    endpoint=endpoint,
    access_token=token,
    api_version="2023-09-01"  # Applies to both /datamap and /catalog
)
```

## Examples

Most Catalog operations are demonstrated in Data Map examples:

- [01_search_assets.py](../examples/data-map/01_search_assets.py) - Entity retrieval
- [02_manage_classifications.py](../examples/data-map/02_manage_classifications.py) - Classifications (Catalog endpoint)
- [03_manage_labels.py](../examples/data-map/03_manage_labels.py) - Labels (Catalog endpoint)
- [01_bulk_operations.py](../examples/advanced/01_bulk_operations.py) - Bulk entity updates

## When to Use Direct Catalog API Calls

Use direct API calls for:

1. **Advanced entity operations** not covered by client methods
2. **Type definition management** (custom types, classifications)
3. **Lineage operations** (not exposed by basic client)
4. **Relationship management** (advanced scenarios)
5. **Bulk operations** with custom payloads

For standard operations (search, get entity, update attributes), use the Data Map client methods.

## Next Steps

- [Data Map API Guide](data-map-api.md) - Primary API guide for catalog operations
- [Data Quality API Guide](data-quality-api.md) - Quality rules and profiling
- [Workflow API Guide](workflow-api.md) - Approval workflows
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
