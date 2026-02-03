# Contributing to Purview API Guide

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

- 🐛 **Report bugs or API issues** you encounter
- 📝 **Improve documentation** with clarifications or examples
- 💡 **Share workarounds** for API limitations
- ✨ **Add new examples** for common use cases
- 🔧 **Enhance client implementations** with better error handling or features
- 🧪 **Add tests** for client functionality

## Getting Started

### 1. Fork and Clone

```bash
git fork https://github.com/yourusername/purview-api-guide
git clone https://github.com/your-username/purview-api-guide.git
cd purview-api-guide
```

### 2. Set Up Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Configure your credentials (for testing)
# Edit .env with your service principal credentials
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Contribution Guidelines

### Code Style

- **Python**: Follow PEP 8 style guide
- **Line length**: 100 characters maximum
- **Docstrings**: Use Google-style docstrings with examples
- **Type hints**: Include type hints for function signatures
- **Comments**: Explain *why*, not *what*

### Example Code Standards

When adding examples:

1. **No hardcoded values**: Use environment variables or user input
2. **Clear comments**: Explain what each section does
3. **Error handling**: Include try/except blocks with helpful messages
4. **User-friendly**: Add print statements showing progress
5. **Tested**: Verify the example works with real credentials

**Good example:**

```python
def main():
    """Demonstrate asset search functionality."""
    # Load endpoint from environment
    endpoint = os.getenv("PURVIEW_ENDPOINT")
    if not endpoint:
        print("ERROR: PURVIEW_ENDPOINT not set. See .env.example")
        return

    # Authenticate
    try:
        token = get_access_token()
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    # Search for assets
    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)
    results = client.search_assets(keywords="sales", limit=10)

    print(f"Found {len(results)} assets")
```

**Bad example:**

```python
# ❌ Don't do this
def main():
    endpoint = "https://my-account.purview.azure.com"  # Hardcoded!
    token = "eyJ0eXAi..."  # Hardcoded token!

    client = PurviewDataMapClient(endpoint=endpoint, access_token=token)
    results = client.search_assets()  # No error handling, no output
```

### Documentation Standards

- **Links**: Always link to official Microsoft documentation
- **Examples**: Include code snippets with expected output
- **Accuracy**: Verify information against current API behavior
- **Clarity**: Write for users new to Purview APIs

### Client Library Standards

- **Docstrings**: Include:
  - Purpose and overview
  - Args with types and descriptions
  - Returns with type and description
  - Raises for common exceptions
  - Example usage code
  - Link to official API documentation

- **Error handling**: Provide helpful error messages with:
  - What went wrong
  - Why it might have happened
  - How to fix it (link to troubleshooting docs)

**Example:**

```python
def search_assets(
    self,
    keywords: str = "*",
    entity_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for data assets in the catalog.

    Args:
        keywords: Search keywords (* for all)
        entity_type: Filter by type (e.g., "azure_sql_table")
        limit: Maximum results (default: 50)

    Returns:
        List of asset dictionaries with id, name, qualifiedName, etc.

    Raises:
        requests.HTTPError: If API request fails

    Example:
        >>> results = client.search_assets(
        ...     keywords="customer",
        ...     entity_type="azure_sql_table"
        ... )

    Official documentation:
    https://learn.microsoft.com/en-us/rest/api/purview/...
    """
```

## Testing

Before submitting:

1. **Test your changes** with real Purview credentials
2. **Verify no hardcoded values** (run `grep -r "purview.azure.com" .` )
3. **Check for secrets** (run `grep -r "eyJ0eXAi" .` for tokens)
4. **Test examples** work from a fresh clone

## Submitting a Pull Request

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add example for X"
   # or "Fix issue with Y"
   # or "Update docs for Z"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request**:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template

### PR Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Example addition

## Testing
How did you test these changes?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tested with real Purview credentials
- [ ] No hardcoded values or secrets
- [ ] Added/updated documentation
- [ ] Examples include error handling
```

## Reporting Issues

When reporting bugs or API issues:

1. **Search existing issues** first
2. **Use issue templates** if available
3. **Include**:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - API endpoint and method
   - Error messages (remove secrets!)
   - API version used

## Community Guidelines

- **Be respectful**: This is an unofficial community project
- **Be helpful**: Share your knowledge and workarounds
- **Be patient**: Maintainers are volunteers
- **Be clear**: Good communication helps everyone

## Questions?

- **General questions**: [GitHub Discussions](https://github.com/yourusername/purview-api-guide/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/yourusername/purview-api-guide/issues)
- **Security issues**: Email maintainers privately (see SECURITY.md)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** 🎉

Every contribution helps make Purview APIs easier to use for everyone.
