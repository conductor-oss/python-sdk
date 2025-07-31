# Release Process

This document outlines the steps to release a new version of the `conductor-python` package to PyPI. Following this process ensures that releases are consistent and stable.

## Summary

The release process is based on the following principles:
- The `main` branch is the source of truth for all releases.
- Releases are triggered by creating and pushing a new git tag.
- The package version is managed in `pyproject.toml`.

## Step-by-Step Guide

### 1. Prepare for Release

Before starting the release process, ensure that:
- All features, fixes, and changes for the new version have been merged into the `main` branch.
- The `main` branch is stable and all automated tests are passing.

### 2. Create a Release Branch

Create a new branch from the `main` branch. This branch will be used to prepare the release.

```bash
# Ensure you are on the main branch and have the latest changes
git checkout main
git pull origin main

# Create a release branch (e.g., release/v1.2.3)
git checkout -b release/vX.Y.Z
```
Replace `X.Y.Z` with the new version number.

### 3. Bump the Package Version

In the release branch, you must update the package version in the `pyproject.toml` file.

1.  Open `pyproject.toml`.
2.  Locate the `version` field under the `[tool.poetry]` section.
3.  Update the version to the new version number (e.g., `version = "1.2.3"`).

Commit the version change. If `poetry.lock` was modified, add it to the commit as well.
```bash
git add pyproject.toml poetry.lock
git commit -m "Bump version to vX.Y.Z"
```

**Important:** This is a critical step. The version in `pyproject.toml` is used by the GitHub Actions pipeline to publish the package.

### 4. Final Testing

Although the `main` branch should be stable, it is good practice to run the full test suite one more time within the release branch to catch any issues related to the version bump.

### 5. Merge the Release Branch into Main

Create a Pull Request (PR) to merge your `release/vX.Y.Z` branch back into `main`.

- Clearly state in the PR title that it's for a release (e.g., "Release vX.Y.Z").
- After the PR is reviewed and approved, merge it.
- Delete the release branch after the merge.

### 6. Create and Push the Git Tag

This is the final step that triggers the deployment pipeline.

1.  First, make sure your local `main` branch is up-to-date with the merge commit from the previous step.
    ```bash
    git checkout main
    git pull origin main
    ```

2.  Create an annotated git tag. The tag name **must** match the version number in `pyproject.toml` and should be prefixed with `v`.
    ```bash
    # Example for version 1.2.3
    git tag -a v1.2.3 -m "Release version 1.2.3"
    ```

3.  Push the tag to the remote repository.
    ```bash
    # Example for version 1.2.3
    git push origin v1.2.3
    ```

### 7. Verify the Release

- Pushing the tag will trigger the "Release" workflow in GitHub Actions.
- Monitor the workflow to ensure it completes successfully.
- Once the workflow is finished, navigate to the project's page on [PyPI](https://pypi.org/project/conductor-python/) to verify that the new version has been published. 