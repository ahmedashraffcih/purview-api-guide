"""
Client for Microsoft Purview Data Quality / Data Governance APIs.

Provides methods for:
- Creating and managing quality rules
- Triggering and monitoring profiling jobs
- Managing business domains and data products
- Viewing quality assessment results

Official documentation:
https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane
"""

from typing import Any, Dict, List, Optional
from clients.base_client import BaseHTTPClient


class PurviewDataQualityClient(BaseHTTPClient):
    """
    Client for Purview Data Quality and Data Governance APIs.

    Note: Data Quality APIs use a different endpoint (api.purview-service.microsoft.com)
    but the same authentication token.

    Example:
        >>> from clients.dataquality_client import PurviewDataQualityClient
        >>> from clients.auth import get_access_token
        >>>
        >>> token = get_access_token()
        >>> client = PurviewDataQualityClient(access_token=token)
        >>>
        >>> # List business domains
        >>> domains = client.list_domains()
        >>> print(f"Found {len(domains)} domains")

    Official documentation:
    https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/business-domain-management
    """

    def __init__(
        self,
        access_token: str,
        endpoint: str = "https://api.purview-service.microsoft.com",
        api_version: str = "2025-09-01-preview"
    ):
        """
        Initialize Data Quality client.

        Args:
            access_token: OAuth2 bearer token (from get_access_token())
            endpoint: Data Quality API endpoint (default: api.purview-service.microsoft.com)
            api_version: API version (default: 2025-09-01-preview)
        """
        super().__init__(base_url=endpoint, access_token=access_token)
        self.api_version = api_version

    # ===== Business Domain Operations =====

    def list_domains(self) -> List[Dict[str, Any]]:
        """
        List all business domains (governance domains) in the account.

        Returns:
            List of domain dictionaries with id, name, description, etc.

        Example:
            >>> domains = client.list_domains()
            >>> for domain in domains:
            ...     print(f"{domain['name']}: {domain['id']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/business-domain-management/list-business-domains
        """
        response = self.get(
            "/datagov/quality/business-domains",
            params={"api-version": self.api_version}
        )
        return response.json().get("value", [])

    def get_domain(self, domain_id: str) -> Dict[str, Any]:
        """
        Get business domain details.

        Args:
            domain_id: Business domain GUID

        Returns:
            Domain dictionary

        Example:
            >>> domain = client.get_domain("domain-guid")
            >>> print(f"Domain: {domain['name']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/business-domain-management/get-business-domain
        """
        response = self.get(
            f"/datagov/quality/business-domains/{domain_id}",
            params={"api-version": self.api_version}
        )
        return response.json()

    # ===== Data Product Operations =====

    def list_data_products(self, domain_id: str) -> List[Dict[str, Any]]:
        """
        List data products in a business domain.

        Args:
            domain_id: Business domain GUID

        Returns:
            List of data product dictionaries

        Example:
            >>> products = client.list_data_products(domain_id="domain-guid")
            >>> for product in products:
            ...     print(f"{product['name']}: {product['id']}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/data-product-management/list-data-products
        """
        response = self.get(
            f"/datagov/quality/business-domains/{domain_id}/data-products",
            params={"api-version": self.api_version}
        )
        return response.json().get("value", [])

    # ===== Quality Rule Operations =====

    def create_rule(
        self,
        business_domain_id: str,
        data_product_id: str,
        data_asset_id: str,
        rule_id: str,
        rule_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a data quality rule.

        Important: rule_body must include "columns" array in typeProperties.
        See docs/api-limitations.md for details.

        Args:
            business_domain_id: Business domain GUID
            data_product_id: Data product GUID
            data_asset_id: Data asset GUID (use Catalog Asset ID, not Data Map GUID)
            rule_id: Unique rule identifier (alphanumeric + underscores)
            rule_body: Rule configuration dictionary

        Returns:
            Created rule dictionary

        Example:
            >>> rule = client.create_rule(
            ...     business_domain_id="domain-guid",
            ...     data_product_id="product-guid",
            ...     data_asset_id="asset-guid",
            ...     rule_id="check_nulls_customer_id",
            ...     rule_body={
            ...         "name": "Check Nulls - Customer ID",
            ...         "type": "CustomSQL",
            ...         "typeProperties": {
            ...             "condition": "SELECT COUNT(*) FROM {table} WHERE customer_id IS NULL",
            ...             "columns": [{"value": "customer_id", "type": "Column"}]
            ...         }
            ...     }
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/rules/create-or-update-rule
        """
        response = self.put(
            f"/datagov/quality/business-domains/{business_domain_id}/"
            f"data-products/{data_product_id}/data-assets/{data_asset_id}/"
            f"rules/{rule_id}",
            json=rule_body,
            params={"api-version": self.api_version}
        )
        return response.json()

    def get_rule(
        self,
        business_domain_id: str,
        data_product_id: str,
        data_asset_id: str,
        rule_id: str
    ) -> Dict[str, Any]:
        """
        Get a quality rule by ID.

        Args:
            business_domain_id: Business domain GUID
            data_product_id: Data product GUID
            data_asset_id: Data asset GUID
            rule_id: Rule identifier

        Returns:
            Rule dictionary

        Example:
            >>> rule = client.get_rule(
            ...     business_domain_id="domain-guid",
            ...     data_product_id="product-guid",
            ...     data_asset_id="asset-guid",
            ...     rule_id="check_nulls_customer_id"
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/rules/get-rule
        """
        response = self.get(
            f"/datagov/quality/business-domains/{business_domain_id}/"
            f"data-products/{data_product_id}/data-assets/{data_asset_id}/"
            f"rules/{rule_id}",
            params={"api-version": self.api_version}
        )
        return response.json()

    def list_rules(
        self,
        business_domain_id: str,
        data_product_id: str,
        data_asset_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all quality rules for a data asset.

        Args:
            business_domain_id: Business domain GUID
            data_product_id: Data product GUID
            data_asset_id: Data asset GUID

        Returns:
            List of rule dictionaries

        Example:
            >>> rules = client.list_rules(
            ...     business_domain_id="domain-guid",
            ...     data_product_id="product-guid",
            ...     data_asset_id="asset-guid"
            ... )
            >>> print(f"Found {len(rules)} rules")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/rules/list-rules
        """
        response = self.get(
            f"/datagov/quality/business-domains/{business_domain_id}/"
            f"data-products/{data_product_id}/data-assets/{data_asset_id}/rules",
            params={"api-version": self.api_version}
        )
        return response.json().get("value", [])

    def delete_rule(
        self,
        business_domain_id: str,
        data_product_id: str,
        data_asset_id: str,
        rule_id: str
    ) -> None:
        """
        Delete a quality rule.

        Args:
            business_domain_id: Business domain GUID
            data_product_id: Data product GUID
            data_asset_id: Data asset GUID
            rule_id: Rule identifier

        Example:
            >>> client.delete_rule(
            ...     business_domain_id="domain-guid",
            ...     data_product_id="product-guid",
            ...     data_asset_id="asset-guid",
            ...     rule_id="check_nulls_customer_id"
            ... )

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/rules/delete-rule
        """
        self.delete(
            f"/datagov/quality/business-domains/{business_domain_id}/"
            f"data-products/{data_product_id}/data-assets/{data_asset_id}/"
            f"rules/{rule_id}",
            params={"api-version": self.api_version}
        )

    # ===== Profiling Operations =====

    def profile_asset(
        self,
        business_domain_id: str,
        data_product_id: str,
        data_asset_id: str,
        profile_config: Dict[str, Any]
    ) -> str:
        """
        Trigger profiling job for a data asset.

        Important: Profiling statistics cannot be retrieved via REST API.
        View results in Purview Portal UI. See docs/api-limitations.md.

        Args:
            business_domain_id: Business domain GUID
            data_product_id: Data product GUID
            data_asset_id: Data asset GUID
            profile_config: Profiling configuration (type, dataSourceId, tables, etc.)

        Returns:
            Profile run ID (extract from response.result.value, not response.id!)

        Example:
            >>> run_id = client.profile_asset(
            ...     business_domain_id="domain-guid",
            ...     data_product_id="product-guid",
            ...     data_asset_id="asset-guid",
            ...     profile_config={
            ...         "type": "AzureSqlDatabase",
            ...         "dataSourceId": "connection-guid",
            ...         "tables": [{"schema": "dbo", "table": "customers"}]
            ...     }
            ... )
            >>> print(f"Profile job started: {run_id}")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/profiling/profile-data-asset
        """
        response = self.post(
            f"/datagov/quality/data-assets/{data_asset_id}:profile",
            json=profile_config,
            params={"api-version": self.api_version}
        )
        result = response.json()

        # Extract run ID from response.result.value (NOT response.id)
        return result.get("result", {}).get("value")

    def get_run_status(
        self,
        business_domain_id: str,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Get profiling or quality scan run status.

        Returns job metadata including status, timestamps, and error messages.
        Does NOT include profiling statistics (not available via API).

        Args:
            business_domain_id: Business domain GUID
            run_id: Run ID from profile_asset() or trigger_quality_scan()

        Returns:
            Run status dictionary with: runId, status, submissionTime, endTime, message

        Example:
            >>> status = client.get_run_status(
            ...     business_domain_id="domain-guid",
            ...     run_id="run-guid"
            ... )
            >>> print(f"Status: {status['status']}")  # Succeeded, Failed, InProgress, etc.

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/run-management/get-run
        """
        response = self.get(
            f"/datagov/quality/business-domains/{business_domain_id}/runs/{run_id}",
            params={"api-version": self.api_version}
        )
        return response.json()

    def list_runs(
        self,
        business_domain_id: str,
        data_asset_id: str,
        run_type: str = "Profile"
    ) -> List[Dict[str, Any]]:
        """
        List profiling or quality scan run history for a data asset.

        Args:
            business_domain_id: Business domain GUID
            data_asset_id: Data asset GUID
            run_type: Run type filter ("Profile" or "Quality")

        Returns:
            List of run dictionaries sorted by submission time (newest first)

        Example:
            >>> runs = client.list_runs(
            ...     business_domain_id="domain-guid",
            ...     data_asset_id="asset-guid",
            ...     run_type="Profile"
            ... )
            >>> for run in runs:
            ...     print(f"{run['runId']}: {run['status']} ({run['submissionTime']})")

        Official documentation:
        https://learn.microsoft.com/en-us/rest/api/purview/datagovernancedataplane/run-management/list-runs
        """
        response = self.get(
            f"/datagov/quality/data-assets/{data_asset_id}/runs",
            params={"api-version": self.api_version, "runType": run_type}
        )

        runs = response.json().get("value", [])

        # Sort by submission time (newest first) - API doesn't guarantee order
        runs.sort(key=lambda r: r.get("submissionTime", ""), reverse=True)

        return runs
