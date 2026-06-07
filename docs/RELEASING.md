# Releasing mayaastrolib

Releases are published to PyPI **automatically** by
`.github/workflows/publish.yml` using PyPI **Trusted Publishing** (OIDC) — no
API token is stored in the repo, in GitHub secrets, or anywhere else.

## One-time setup (PyPI side)

Do this once. It tells PyPI to trust releases coming from this repo's workflow.

1. Go to **https://pypi.org/manage/project/mayaastrolib/settings/publishing/**
   (log in as the project owner).
2. Under **"Add a new trusted publisher" → GitHub**, enter:
   - **Owner:** `ranganc007`
   - **Repository name:** `mayaastrolib`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
3. Save.

Optionally, in the GitHub repo (**Settings → Environments**), create an
environment named **`pypi`** and add protection rules (e.g. required
reviewers) so a human must approve each publish.

## Cutting a release

1. Bump `version` in `pyproject.toml` and add a dated section to
   `CHANGELOG.md`.
2. Commit on `development`, fast-forward `master`, push both.
3. Tag and create the GitHub release:
   ```sh
   git tag -a vX.Y.Z -m "mayaastrolib X.Y.Z"
   git push origin vX.Y.Z
   gh release create vX.Y.Z -R ranganc007/mayaastrolib --title "..." --notes "..." --latest
   ```
4. Publishing the release triggers `publish.yml`, which builds, validates,
   **verifies the wheel computes a real chart**, and publishes to PyPI.

## Manual fallback

If Trusted Publishing is unavailable, build and upload by hand:

```sh
python -m build
twine check dist/*
twine upload dist/*          # username: __token__ , password: a PyPI API token
```
