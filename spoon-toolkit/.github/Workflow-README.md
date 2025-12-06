# GitHub Actions Workflows for Spoon Toolkit

This directory contains GitHub Actions workflows for automated testing, building, and publishing of the Spoon Toolkit Python package.

## Workflows Overview

### 1. CI Workflow (`ci.yml`)
- **Trigger**: Push to `main`/`develop` branches, Pull Requests
- **Purpose**: Build package and verify compatibility across Python versions
- **Features**:
  - Multi-Python version build verification (3.11, 3.12, 3.13)
  - Package build and validation
  - Artifact upload for releases
  - No testing - focuses on build verification only

### 2. Release Workflow (`release.yml`)
- **Trigger**: GitHub release published
- **Purpose**: Automatically publish to PyPI using trusted publishing
- **Features**:
  - Separated build and publish jobs
  - Trusted publishing with PyPI
  - Environment protection for secure publishing
  - Official PyPI publishing action

### 3. Version Bump Workflow (`version-bump.yml`)
- **Trigger**: Manual workflow dispatch
- **Purpose**: Automated version management and tagging
- **Features**:
  - Support for patch/minor/major version bumps
  - Custom version input option
  - Automatic commit and tag creation
  - Push to repository

## Setup Instructions

### 1. PyPI Trusted Publishing Setup

For trusted publishing, you need to configure PyPI to trust your GitHub repository:

1. Go to [PyPI](https://pypi.org/) and log in
2. Go to Account Settings → Publishing
3. Add your GitHub repository as a trusted publisher
4. Configure the environment name as `pypi` in your repository settings

**Note**: No API tokens needed for trusted publishing!

### 2. Repository Settings

Ensure your repository has the following settings:

- **Actions permissions**: Allow actions to create and approve pull requests
- **Workflow permissions**: Read and write permissions for GITHUB_TOKEN

### 3. Branch Protection (Recommended)

Set up branch protection for `main` branch:
- Require status checks to pass
- Require branches to be up to date
- Include administrators in restrictions

## Usage

### Automatic Release Process

1. **Version Bump**: Use the Version Bump workflow to increment version
   - Go to Actions → Version Bump and Tag → Run workflow
   - Choose version type (patch/minor/major) or enter custom version
   - **Note**: Even if you specify the same version, it will still create a commit and tag

2. **Create GitHub Release**: After version bump, create a GitHub release
   - Go to GitHub Releases → Create new release
   - Use the tag created by the version bump workflow
   - Publish the release

3. **Automatic Publishing**: When the GitHub release is published, the workflow automatically:
   - Builds the package
   - Publishes to PyPI using trusted publishing
   - **Guaranteed**: Package will be published even if version didn't change
   - No manual PyPI token management needed

### Manual Version Management

If you prefer manual version management:

1. Update version in `pyproject.toml`
2. Commit changes: `git commit -m "Bump version to x.y.z"`
3. Create tag: `git tag vx.y.z`
4. Push: `git push && git push --tags`

## Workflow Details

### CI Workflow
```yaml
# Runs on every push/PR
- Multi-version Python build verification
- Package build and twine check
- Upload build artifacts
- No testing - focuses on build verification only
```

### Release Workflow
```yaml
# Runs on GitHub release published
# Job 1: Build distributions
- Checkout code
- Setup Python 3.11
- Build package (sdist + wheel)
- Upload build artifacts

# Job 2: Publish to PyPI (trusted publishing)
- Download build artifacts
- Publish to PyPI using trusted publishing
- Environment protection enabled
```

### Version Bump Workflow
```yaml
# Manual trigger
- Checkout with write permissions
- Install bump2version
- Calculate new version
- Update pyproject.toml
- Commit and tag
- Push changes
```

## File Structure

```
.github/
├── workflows/
│   ├── ci.yml           # Continuous Integration
│   ├── release.yml      # PyPI Publishing
│   └── version-bump.yml # Version Management
└── README.md            # This documentation
```

## Dependencies

The following tools are used in the workflows:

- `build`: Package building
- `twine`: PyPI uploading
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `bump2version`: Version management

## Troubleshooting

### Common Issues

1. **PyPI Upload Fails**
   - Check `PYPI_API_TOKEN` secret is set correctly
   - Verify token has upload permissions for the project

2. **Tests Fail**
   - Check Python version compatibility
   - Ensure all dependencies are in `requirements.txt`
   - Verify test configuration in `pytest.ini`

3. **Build Fails**
   - Check `pyproject.toml` configuration
   - Ensure all required files are included
   - Verify package structure matches `setuptools` configuration

### Debug Mode

To debug workflow issues:
1. Go to Actions tab in GitHub
2. Select the failed workflow run
3. Check logs for each step
4. Use `debug` logging level if available

## Contributing

When contributing to the workflows:

1. Test changes on a feature branch first
2. Update this documentation if workflows change
3. Ensure backward compatibility
4. Follow GitHub Actions best practices

## Security Notes

- Never commit secrets to the repository
- Use repository secrets for sensitive data
- Regularly rotate API tokens
- Limit token scopes to minimum required permissions
