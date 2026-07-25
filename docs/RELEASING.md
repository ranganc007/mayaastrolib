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

Trusted Publishing is the only standing path — **no API token is kept on disk
or in GitHub secrets.** If you ever must upload by hand (CI down, emergency
hotfix), mint a **fresh, project-scoped** token at upload time and revoke it
immediately afterwards. Never keep a long-lived token lying around "just in
case"; a stored upload credential is a liability with no offsetting benefit
once Trusted Publishing works.

```sh
python -m build
twine check dist/*
# Create a token scoped to the `mayaastrolib` project at
# https://pypi.org/manage/account/token/ , use it once, then delete it.
twine upload dist/*          # username: __token__ , password: the fresh token
```

## ReadTheDocs (one-time, manual)

`.readthedocs.yaml` is committed and the Sphinx build is wired up, but
**publishing still requires enabling the project once in the RTD dashboard** —
that is a dashboard action, not a repo change:

1. Sign in at <https://readthedocs.org> with the GitHub account that owns the
   repo and *Import a Project* → `ranganc007/mayaastrolib`.
2. RTD picks up `.readthedocs.yaml` automatically; no dashboard build settings
   need changing.
3. Enable *Build pull requests for this project* if you want doc previews on PRs.

The build runs with `fail_on_warning: true`, matching the local gate
(`sphinx-build -W`). Reproduce a failure locally with:

```sh
pip install -e ".[docs]"
python -m sphinx -W -b html docs/source docs/_build
```
