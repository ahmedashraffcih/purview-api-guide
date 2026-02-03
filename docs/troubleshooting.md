# Troubleshooting Guide

Common errors, their causes, and solutions when working with Microsoft Purview REST APIs.

## Authentication Errors

### 401 Unauthorized

**Error Message**:
```
HTTP 401 Unauthorized
{
  "error": {
    "code": "InvalidAuthenticationToken",
    "message": "Access token is invalid or expired"
  }
}
```

**Common Causes**:

1. **Expired token** (tokens last ~60 minutes)
   ```python
   # Solution: Refresh token
   from clients.auth import get_access_token
   token = get_access_token()  # Gets fresh token
   ```

2. **Wrong token scope**
   ```python
   # ❌ Incorrect
   scope = "https://graph.microsoft.com/.default"

   # ✅ Correct
   scope = "https://purview.azure.net/.default"
   ```

3. **Invalid client secret**
   ```bash
   # Verify credentials
   echo $CLIENT_SECRET | wc -c  # Should be > 0

   # Test authentication
   python -c "from clients.auth import get_access_token; print(len(get_access_token()))"
   ```

4. **Tenant ID mismatch**
   ```bash
   # Ensure TENANT_ID matches your Azure AD tenant
   # Find your tenant ID: Azure Portal → Azure Active Directory → Overview
   ```

**Resolution Steps**:
1. Verify `.env` file has correct credentials
2. Ensure no extra spaces/newlines in `.env` values
3. Regenerate client secret if uncertain
4. Test with `curl`:
   ```bash
   curl -X POST https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=$CLIENT_ID" \
     -d "client_secret=$CLIENT_SECRET" \
     -d "scope=https://purview.azure.net/.default" \
     -d "grant_type=client_credentials"
   ```

---

### 403 Forbidden

**Error Message**:
```
HTTP 403 Forbidden
{
  "error": {
    "code": "AuthorizationFailed",
    "message": "The client does not have authorization to perform action"
  }
}
```

**Common Causes**:

1. **Missing RBAC role assignment**

   **For Data Map operations**:
   - Navigate to: **Purview Portal** → **Data Map** → **Collections** → **Role assignments**
   - Assign appropriate role (Data Reader, Data Curator, etc.)
   - Role on the specific collection containing your assets

   **For Data Quality operations**:
   - Navigate to: **Purview Portal** → **Unified Catalog** → **Catalog Management** → **Governance Domains** → **Role assignments**
   - Assign **Data Quality Steward** role

2. **Role not yet propagated** (can take 5-10 minutes)
   ```python
   import time
   print("Waiting for RBAC propagation...")
   time.sleep(600)  # Wait 10 minutes after role assignment
   ```

3. **Role assigned to user instead of service principal**
   - Ensure the service principal (app registration) has the role, not your user account
   - In role assignment, search for the app registration name, not your email

4. **Wrong collection scope**
   - Data Map roles are collection-specific
   - Asset might be in a different collection than where role was assigned

**Resolution Steps**:
1. Verify service principal has correct role:
   ```bash
   # Get service principal object ID
   az ad sp show --id $CLIENT_ID --query objectId -o tsv

   # Check role assignments (requires admin access)
   # Use Purview Portal UI to verify
   ```

2. Check role assignment in Purview Portal (logged in as admin)
3. Wait 10 minutes after assignment
4. Try a read-only operation first (search) to verify access

**Required Roles by Operation**:

| Operation | Minimum Role | Assignment Location |
|-----------|--------------|---------------------|
| Search assets | Data Reader | Data Map → Collections |
| Get entity | Data Reader | Data Map → Collections |
| Update entity description | Data Curator | Data Map → Collections |
| Add classifications | Data Curator | Data Map → Collections |
| Create glossary terms | Data Curator | Data Map → Collections |
| Register data sources | Data Source Administrator | Data Map → Collections |
| Create quality rules | Data Quality Steward | Unified Catalog → Governance Domains |
| Run profiling | Data Quality Steward | Unified Catalog → Governance Domains |
| Create workflows | Workflow Admin | Management → Role assignments |

---

## API Endpoint Errors

### 404 Not Found

**Error Message**:
```
HTTP 404 Not Found
{
  "error": {
    "code": "ResourceNotFound",
    "message": "The specified resource does not exist"
  }
}
```

**Common Causes**:

1. **Incorrect endpoint URL format**
   ```python
   # ❌ Incorrect
   endpoint = "https://account-name.purview.azure.com/"  # Trailing slash
   endpoint = "https://web.purview.azure.com/..."  # Portal URL, not API

   # ✅ Correct
   endpoint = "https://account-name.purview.azure.com"
   ```

2. **Wrong API version**
   ```python
   # Check API version in URL
   # Data Map: api-version=2023-09-01
   # Data Quality: api-version=2025-09-01-preview
   ```

3. **Entity GUID doesn't exist**
   ```python
   # Verify GUID with search first
   results = client.search_assets(keywords="table-name")
   if results:
       guid = results[0]["id"]
   else:
       print("Entity not found in catalog")
   ```

4. **Endpoint not available in this API version** (e.g., partial update)
   - See [API Limitations](api-limitations.md#2-partial-entity-update-endpoint-returns-404)

**Resolution Steps**:
1. Print full URL before making request
2. Check official API documentation for correct endpoint path
3. Verify entity exists with search or list operation first
4. Use network debugging to see actual request:
   ```python
   import logging
   import http.client as http_client

   http_client.HTTPConnection.debuglevel = 1
   logging.basicConfig(level=logging.DEBUG)
   ```

---

### 400 Bad Request

**Error Message**:
```
HTTP 400 Bad Request
{
  "error": {
    "code": "InvalidRequest",
    "message": "The request is invalid"
  }
}
```

**Common Causes**:

1. **Missing required parameters**
   ```python
   # ❌ Missing api-version
   response = requests.get(f"{endpoint}/datamap/api/atlas/v2/types/typedefs")

   # ✅ Include api-version
   response = requests.get(
       f"{endpoint}/datamap/api/atlas/v2/types/typedefs",
       params={"api-version": "2023-09-01"}
   )
   ```

2. **Invalid JSON body**
   ```python
   # Validate JSON before sending
   import json

   try:
       json.dumps(request_body)
   except TypeError as e:
       print(f"Invalid JSON: {e}")
   ```

3. **Wrong Content-Type header**
   ```python
   # Ensure correct headers
   headers = {
       "Content-Type": "application/json",
       "Authorization": f"Bearer {token}"
   }
   ```

4. **Deprecated endpoint** (e.g., basic search)
   - See [API Limitations](api-limitations.md#1-basic-search-endpoint-returns-400)

**Resolution Steps**:
1. Check request body structure matches API docs
2. Validate required fields are present
3. Use API reference documentation for examples
4. Enable debug logging to see full request

---

### 429 Too Many Requests

**Error Message**:
```
HTTP 429 Too Many Requests
Retry-After: 60
```

**Cause**: Rate limit exceeded

**Resolution**:
```python
# Clients automatically retry with exponential backoff
# Manual implementation:
import time

def request_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        response = func()
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
        return response
    raise Exception("Max retries exceeded")
```

**Prevention**:
- Add delays between bulk operations: `time.sleep(1)`
- Batch requests when possible
- Use pagination with reasonable page sizes

---

### 500 Internal Server Error

**Error Message**:
```
HTTP 500 Internal Server Error
```

**Causes**:
- Transient service issue
- Bug in API backend
- Malformed request that passed validation

**Resolution**:
1. **Retry the request** (may be transient)
   ```python
   # Clients automatically retry 5xx errors
   ```

2. **Simplify the request** (if complex query)
   ```python
   # Try with minimal parameters
   response = client.search_assets(keywords="*", limit=10)
   ```

3. **Report to Microsoft** if persistent
   - Include request/response details
   - Submit via Azure Support

---

## Data Quality Errors

### DQ-MissingColumn

**Error Message**:
```
DQ-MissingColumn: Rule validation failed - missing column metadata
```

**Cause**: Quality rule missing `columns` array in API payload

**Solution**: See [API Limitations - Missing Columns Array](api-limitations.md#6-data-quality-rules-missing-columns-array)

```python
rule = {
    "name": "Check Nulls",
    "type": "CustomSQL",
    "typeProperties": {
        "condition": "SELECT COUNT(*) FROM {table} WHERE col IS NULL",
        "columns": [{"value": "col", "type": "Column"}]  # ← Required
    }
}
```

---

### DQ-DSL-BuildError

**Error Message**:
```
DQ-DSL-BuildError: Unable to build job DSL - configuration mismatch
```

**Causes**:
1. Wrong `type` in profile body (must match data source)
2. Invalid `dataSourceId` (not registered with domain)
3. Incorrect schema structure

**Solution**: See [API Limitations - Profiling Build Errors](api-limitations.md#8-profiling-job-dq-dsl-builderror-errors)

```python
# Check asset metadata first
metadata = client.get(f"/datagov/quality/data-assets/{asset_id}/asset-metadata")
print(f"Use type: {metadata['type']}")
```

---

## Entity / Classification Errors

### ATLAS-404-00-007

**Error Message**:
```
ATLAS-404-00-007: Given typename <business-metadata-type> is not applicable for entity type <entity-type>
```

**Cause**: Business metadata type not configured for this entity type

**Solution**: See [API Limitations - Business Metadata Applicability](api-limitations.md#3-business-metadata-type-applicability-restrictions)

```python
# Check applicability before attaching
typedef = client.get(f"/datamap/api/atlas/v2/types/typedef/name/{bm_type_name}")
applicable = typedef["businessMetadataDefs"][0]["applicableEntityTypes"]

if entity_type in applicable:
    client.set_business_metadata(guid, bm_type_name, attributes)
else:
    print(f"Cannot attach {bm_type_name} to {entity_type}")
```

---

### Classification Already Associated

**Error Message**:
```
Classification <name> is already associated with entity <guid>
```

**Cause**: Attempting to add duplicate classification

**Solution**:
```python
# Check existing classifications first
entity = client.get_entity(guid)
existing = [c["typeName"] for c in entity["entity"]["classifications"]]

new_classifications = [c for c in classifications if c not in existing]
if new_classifications:
    client.add_classifications(guid, new_classifications)
```

---

## Connection / Network Errors

### Connection Timeout

**Error**:
```
requests.exceptions.ConnectTimeout: Connection to <endpoint> timed out
```

**Causes**:
1. Corporate firewall/proxy blocking request
2. Incorrect endpoint URL
3. Network connectivity issue

**Resolution**:
```python
# Configure proxy if needed
import os
os.environ['HTTP_PROXY'] = 'http://proxy:port'
os.environ['HTTPS_PROXY'] = 'http://proxy:port'

# Increase timeout
response = requests.get(url, timeout=60)  # Default is often 10s

# Test connectivity
import socket
socket.create_connection(("purview.azure.com", 443), timeout=5)
```

---

### SSL Certificate Verification Failed

**Error**:
```
requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Causes**:
- Corporate proxy with SSL inspection
- Outdated CA certificates

**Resolution**:
```bash
# Update CA certificates (macOS)
/Applications/Python\ 3.x/Install\ Certificates.command

# Ubuntu/Debian
sudo apt-get install --reinstall ca-certificates

# Temporary workaround (NOT for production)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Pass verify=False to requests (insecure)
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
import http.client as http_client

# Enable HTTP debug
http_client.HTTPConnection.debuglevel = 1

# Enable requests debug
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)
```

### Inspect Full Request/Response

```python
import requests

response = requests.get(url, headers=headers)

# Print details
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Body: {response.text[:500]}")  # First 500 chars
```

### Test with curl

```bash
# Get token
TOKEN=$(python -c "from clients.auth import get_access_token; print(get_access_token())")

# Test endpoint
curl -X GET "https://your-account.purview.azure.com/datamap/api/atlas/v2/types/typedefs?api-version=2023-09-01" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -v  # Verbose output
```

---

## Getting Help

If you're still stuck:

1. **Check documentation**:
   - [Getting Started Guide](getting-started.md)
   - [API Limitations](api-limitations.md)
   - [Official Microsoft Docs](https://learn.microsoft.com/en-us/purview/)

2. **Search existing issues**: [GitHub Issues](https://github.com/yourusername/purview-api-guide/issues)

3. **Ask the community**: [GitHub Discussions](https://github.com/yourusername/purview-api-guide/discussions)

4. **Open a new issue**: Include:
   - Full error message
   - Code snippet (remove credentials!)
   - API endpoint and method
   - Expected vs actual behavior

5. **Official support**: Submit Azure support ticket via Azure Portal

---

**Last Updated**: 2026-02-03
