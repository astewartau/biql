# Setting up PyPI Publishing

This guide explains how to set up automatic PyPI publishing for BIQL releases.

## Prerequisites

1. **PyPI Account**: Create accounts at:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [Test PyPI](https://test.pypi.org/account/register/) (testing)

2. **API Tokens**: Create API tokens for both accounts:
   - PyPI: Account settings → API tokens → Add API token
   - Test PyPI: Account settings → API tokens → Add API token

## GitHub Repository Setup

### 1. Add Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `PYPI_API_TOKEN` | `pypi-xxx...` | Your PyPI API token |
| `TEST_PYPI_API_TOKEN` | `pypi-xxx...` | Your Test PyPI API token |

### 2. Configure PyPI Trusted Publishers (Recommended)

Instead of API tokens, you can use PyPI's trusted publisher feature:

1. Go to [PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/)
2. Add a new trusted publisher with:
   - **Repository**: `yourusername/biql`
   - **Workflow**: `publish.yml`
   - **Environment**: `pypi`

3. Repeat for Test PyPI

### 3. Update Repository URLs

Update these files with your actual repository information:

#### `setup.py`:
```python
url="https://github.com/yourusername/biql",
```

#### `pyproject.toml`:
```toml
[project.urls]
Homepage = "https://github.com/yourusername/biql"
Repository = "https://github.com/yourusername/biql"
```

#### `docs/_config.yml`:
```yaml
url: "https://yourusername.github.io"
repository: "yourusername/biql"
```

## Release Process

### Automatic (Recommended)

1. **Create a Release**:
   ```bash
   # Update version and create tag
   python scripts/release.py 0.2.0
   
   # Push to GitHub
   git push && git push --tags
   ```

2. **Create GitHub Release**:
   - Go to: https://github.com/yourusername/biql/releases/new
   - Select the tag you just created
   - Add release notes
   - Click "Publish release"

3. **Automatic Publishing**:
   - GitHub Actions will automatically build and test the package
   - If tests pass, it will publish to PyPI
   - The package will be available at: https://pypi.org/project/biql/

### Manual Testing

To test publishing to Test PyPI first:

1. **Trigger Test PyPI Workflow**:
   - Go to Actions → Publish to PyPI
   - Click "Run workflow"
   - Check "Publish to Test PyPI"
   - Run workflow

2. **Test Installation**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ biql
   ```

## Workflow Features

### Automated Testing
- Tests on Python 3.8-3.12
- Tests on Ubuntu, Windows, macOS
- Code coverage reporting
- CLI functionality testing

### Security
- Uses PyPI trusted publishers (no long-lived tokens)
- Only publishes on official releases
- Validates package before publishing
- Tests installation on multiple platforms

### Build Process
- Builds source distribution and wheel
- Validates package metadata
- Tests installation from built packages
- Uploads to appropriate PyPI index

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check API tokens or trusted publisher setup
2. **Version already exists**: Update version number
3. **Build failures**: Check package metadata and dependencies
4. **Import errors**: Verify package structure and entry points

### Testing Locally

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Test upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ biql
```

## GitHub Actions Status

Check these workflows for issues:

- **Tests**: Runs on every push/PR
- **Lint**: Code quality checks  
- **Publish**: Only runs on releases
- **Docs**: Builds documentation

All workflows are configured to work together for a complete CI/CD pipeline.