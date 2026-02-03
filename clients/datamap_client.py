"""
Client for Microsoft Purview Data Map and Catalog (Atlas) APIs.

Provides high-level methods for:
- Entity search and retrieval
- Classifications and labels
- Business metadata
- Glossary term management
- Entity relationships

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane
"""

from typing import Any, Dict, List, Optional
from clients.base_client import BaseHTTPClient


class PurviewDataMapClient(BaseHTTPClient):
    """
    Client for Purview Data Map and Catalog (Atlas) APIs.

    This client provides convenient methods for working with Purview's data catalog,
    including searching for assets, managing classifications, and updating metadata.

    Example:
        >>> from clients.datamap_client import PurviewDataMapClient
        >>> from clients.auth import get_access_token
        >>>
        >>> token = get_access_token()
        >>> client = PurviewDataMapClient(
        ...     endpoint="https://your-account.purview.azure.com",
        ...     access_token=token
        ... )
        >>>
        >>> # Search for assets
        >>> results = client.search_assets(keywords="sales", entity_type="azure_sql_table")
        >>> print(f"Found {len(results)} assets")

    Official documentation:
    https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/discovery
    """

    def __init__(
        self,
        endpoint: str,
        access_token: str,
        api_version: str = "2023-09-01"
    ):
        """
        Initialize Data Map client.

        Args:
            endpoint: Purview account endpoint (e.g., https://account.purview.azure.com)
            access_token: OAuth2 bearer token (from get_access_token())
            api_version: API version for Data Map/Catalog endpoints (default: 2023-09-01)
        """
        super().__init__(base_url=endpoint, access_token=access_token)
        self.api_version = api_version

    # ===== Search Operations =====

    def search_assets(
        self,
        keywords: str = "*",
        entity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for data assets in the catalog.

        Note: Uses POST /datamap/api/search/query (not the basic search endpoint,
        which returns 400 in some environments).

        Args:
            keywords: Search keywords (* for all assets)
            entity_type: Filter by entity type (e.g., "azure_sql_table", "databricks_table")
            limit: Maximum number of results (default: 50)

        Returns:
            List of asset dictionaries with keys: id, name, qualifiedName, typeName, etc.

        Example:
            >>> results = client.search_assets(keywords="customer", entity_type="azure_sql_table")
            >>> for asset in results:
            ...     print(f"{asset['name']} - {asset['qualifiedName']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/discovery/query
        """
        body = {
            "keywords": keywords,
            "limit": limit,
        }

        if entity_type:
            body["filter"] = {"entityType": entity_type}

        response = self.post(
            "/datamap/api/search/query",
            json=body,
            params={"api-version": self.api_version}
        )

        data = response.json()
        return data.get("value", [])

    def find_entity_by_qualified_name(
        self,
        qualified_name: str,
        entity_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find an entity by its qualified name.

        Qualified name format depends on entity type:
        - Azure SQL: mssql://server.database.windows.net/database/schema/table
        - Databricks: databricks://workspace/catalog.schema.table
        - ADLS Gen2: https://account.dfs.core.windows.net/container/path

        Args:
            qualified_name: Entity qualified name
            entity_type: Entity type (optional, helps narrow search)

        Returns:
            Entity dictionary with guid, name, attributes, etc., or None if not found

        Example:
            >>> entity = client.find_entity_by_qualified_name(
            ...     qualified_name="mssql://server.database.windows.net/db/dbo/customers"
            ... )
            >>> if entity:
            ...     print(f"Found entity GUID: {entity['id']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane/discovery/query
        """
        # Search by exact qualified name
        body = {
            "keywords": qualified_name,
            "limit": 50,
        }

        if entity_type:
            body["filter"] = {"entityType": entity_type}

        response = self.post(
            "/datamap/api/search/query",
            json=body,
            params={"api-version": self.api_version}
        )

        results = response.json().get("value", [])

        # Find exact match
        for result in results:
            if result.get("qualifiedName") == qualified_name:
                return result

        return None

    # ===== Entity Operations =====

    def get_entity(self, guid: str) -> Dict[str, Any]:
        """
        Get entity details by GUID.

        Returns full entity structure including attributes, classifications,
        business metadata, and referred entities (e.g., columns).

        Args:
            guid: Entity GUID

        Returns:
            Entity dictionary with structure:
            {
                "entity": {"guid": "...", "typeName": "...", "attributes": {...}},
                "referredEntities": {"column-guid": {...}, ...}
            }

        Example:
            >>> entity = client.get_entity("12345678-1234-1234-1234-123456789012")
            >>> print(f"Name: {entity['entity']['attributes']['name']}")
            >>> print(f"Description: {entity['entity']['attributes'].get('description', 'N/A')}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/get-by-guid
        """
        response = self.get(
            f"/catalog/api/atlas/v2/entity/guid/{guid}",
            params={"api-version": self.api_version}
        )
        return response.json()

    def create_or_update_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update an entity.

        Note: This is the workaround for the missing partial update endpoint.
        Get the full entity, modify it, and PUT it back.

        Args:
            entity: Complete entity structure with guid, typeName, attributes, etc.

        Returns:
            Update response with mutatedEntities and guidAssignments

        Example:
            >>> # Get entity
            >>> entity = client.get_entity(guid)
            >>> # Modify attribute
            >>> entity['entity']['attributes']['description'] = "New description"
            >>> # Update
            >>> result = client.create_or_update_entity(entity['entity'])

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/create-or-update
        """
        response = self.post(
            "/catalog/api/atlas/v2/entity",
            json={"entity": entity},
            params={"api-version": self.api_version}
        )
        return response.json()

    # ===== Convenience Methods =====

    def set_description(self, guid: str, description: str) -> Dict[str, Any]:
        """
        Set entity description (convenience method).

        Uses full entity update as workaround for missing partial update endpoint.

        Args:
            guid: Entity GUID
            description: New description text

        Returns:
            Update response

        Example:
            >>> client.set_description(
            ...     guid="12345678-1234-1234-1234-123456789012",
            ...     description="Customer data from CRM system"
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/create-or-update
        """
        # Get full entity
        entity_response = self.get_entity(guid)
        entity = entity_response["entity"]

        # Update description
        entity["attributes"]["description"] = description

        # PUT back
        return self.create_or_update_entity(entity)

    # ===== Classifications =====

    def add_classifications(
        self,
        guid: str,
        classification_names: List[str]
    ) -> None:
        """
        Add classifications to an entity.

        Classifications are tags like "PII", "Confidential", "Sensitive", etc.

        Args:
            guid: Entity GUID
            classification_names: List of classification type names

        Example:
            >>> client.add_classifications(
            ...     guid="12345678-1234-1234-1234-123456789012",
            ...     classification_names=["PII", "Confidential"]
            ... )

        Note: Check existing classifications first to avoid "already associated" errors.
        See docs/api-limitations.md for details.

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/add-classification
        """
        classifications = [{"typeName": name} for name in classification_names]

        self.post(
            f"/catalog/api/atlas/v2/entity/guid/{guid}/classifications",
            json=classifications,
            params={"api-version": self.api_version}
        )

    def get_classifications(self, guid: str) -> List[Dict[str, Any]]:
        """
        Get classifications for an entity.

        Args:
            guid: Entity GUID

        Returns:
            List of classification dictionaries

        Example:
            >>> classifications = client.get_classifications(guid)
            >>> for c in classifications:
            ...     print(c['typeName'])

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/get-classifications
        """
        response = self.get(
            f"/catalog/api/atlas/v2/entity/guid/{guid}/classifications",
            params={"api-version": self.api_version}
        )
        return response.json()

    # ===== Labels =====

    def add_labels(self, guid: str, labels: List[str]) -> None:
        """
        Add labels to an entity.

        Labels are free-text tags for organizing and filtering assets.

        Args:
            guid: Entity GUID
            labels: List of label strings

        Example:
            >>> client.add_labels(
            ...     guid="12345678-1234-1234-1234-123456789012",
            ...     labels=["Production", "CustomerData", "Daily"]
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/add-labels
        """
        self.put(
            f"/catalog/api/atlas/v2/entity/guid/{guid}/labels",
            json=labels,
            params={"api-version": self.api_version}
        )

    def remove_labels(self, guid: str, labels: List[str]) -> None:
        """
        Remove labels from an entity.

        Args:
            guid: Entity GUID
            labels: List of label strings to remove

        Example:
            >>> client.remove_labels(guid, ["Deprecated"])

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/remove-labels
        """
        self.delete(
            f"/catalog/api/atlas/v2/entity/guid/{guid}/labels",
            params={"api-version": self.api_version}
        )

    # ===== Business Metadata =====

    def set_business_metadata(
        self,
        guid: str,
        business_metadata_name: str,
        attributes: Dict[str, Any]
    ) -> None:
        """
        Set business metadata attributes on an entity.

        Business metadata types must be pre-created in Purview and configured
        as applicable to the entity type. See docs/api-limitations.md for details.

        Args:
            guid: Entity GUID
            business_metadata_name: Business metadata type name
            attributes: Dictionary of attribute key-value pairs

        Example:
            >>> client.set_business_metadata(
            ...     guid="12345678-1234-1234-1234-123456789012",
            ...     business_metadata_name="DataQuality",
            ...     attributes={
            ...         "completeness": "95%",
            ...         "accuracy": "98%",
            ...         "last_validated": "2026-02-01"
            ...     }
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity/add-or-update-business-metadata
        """
        body = {business_metadata_name: attributes}

        self.post(
            f"/catalog/api/atlas/v2/entity/guid/{guid}/businessmetadata",
            json=body,
            params={"api-version": self.api_version}
        )

    # ===== Glossary Operations =====

    def create_glossary_term(
        self,
        name: str,
        glossary_guid: str,
        description: Optional[str] = None,
        parent_term_guid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a glossary term.

        Args:
            name: Term name
            glossary_guid: GUID of the glossary to create term in
            description: Optional term description
            parent_term_guid: Optional parent term GUID (for hierarchical terms)

        Returns:
            Created term dictionary with guid

        Example:
            >>> term = client.create_glossary_term(
            ...     name="Customer Lifetime Value",
            ...     glossary_guid="glossary-guid",
            ...     description="Total revenue expected from a customer"
            ... )
            >>> print(f"Created term: {term['guid']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/glossary/create-glossary-term
        """
        body = {
            "name": name,
            "anchor": {"glossaryGuid": glossary_guid}
        }

        if description:
            body["longDescription"] = description

        if parent_term_guid:
            body["parentTerm"] = {"termGuid": parent_term_guid}

        response = self.post(
            "/catalog/api/atlas/v2/glossary/term",
            json=body,
            params={"api-version": self.api_version}
        )
        return response.json()

    def list_glossaries(self) -> List[Dict[str, Any]]:
        """
        List all glossaries in the account.

        Returns:
            List of glossary dictionaries with guid, name, etc.

        Example:
            >>> glossaries = client.list_glossaries()
            >>> for g in glossaries:
            ...     print(f"{g['name']}: {g['guid']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/catalogdataplane/glossary/list-glossaries
        """
        response = self.get(
            "/catalog/api/atlas/v2/glossary",
            params={"api-version": self.api_version}
        )
        return response.json()
