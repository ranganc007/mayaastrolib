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

## Maintainer checklist — cutting 1.0.0

Everything below the line has been prepared and verified on the
`v1.0-08-cut-release` branch. The tag and the GitHub Release are deliberately
**not** automated: publishing to PyPI is irreversible (a version can never be
re-uploaded), so it stays a reviewed human action.

Prepared and verified already:

- [x] `pyproject.toml` version is `1.0.0`; `Development Status :: 5 -
      Production/Stable`; `Typing :: Typed`; `requires-python >=3.10`; URLs and
      README long-description in place.
- [x] `CHANGELOG.md` has a dated `## [1.0.0]` section leading with the
      "Migrating from 0.x" guide.
- [x] Pre-flight gate: ruff format + ruff check + mypy clean; full suite green
      with coverage well above the 80% floor; `python -m build` +
      `twine check` clean; the wheel contains only `mayaastrolib`; **no
      `DeprecationWarning` remains anywhere in the package**;
      `docs/API-STABILITY.md` present and enforced by `tests/test_public_api.py`.
- [x] `publish.yml` verifies the release tag matches the `pyproject.toml`
      version before publishing, so a stale version cannot ship under a new tag.

To actually release:

```sh
# 1. Land the release prep (it is on v1.0-08-cut-release, unmerged by design)
git checkout development
git merge --ff-only v1.0-08-cut-release
git push origin development

# 2. Promote to master — master is the release branch
git checkout master
git merge --ff-only development
git push origin master

# 3. Tag it
git tag -a v1.0.0 -m "mayaastrolib 1.0.0 — frozen public API, deprecations cleared"
git push origin v1.0.0

# 4. Create the GitHub Release. Publishing it fires publish.yml, which builds,
#    checks the tag against the version, smoke-tests the wheel in a clean venv,
#    and uploads to PyPI via Trusted Publishing (OIDC — no token anywhere).
gh release create v1.0.0 \
  --title "mayaastrolib 1.0.0" \
  --notes-file <(sed -n '/^## \[1.0.0\]/,/^## \[0.5.0\]/p' CHANGELOG.md | sed '$d')

# 5. Watch it
gh run watch --repo ranganc007/mayaastrolib
```

Afterwards:

- [ ] Confirm <https://pypi.org/project/mayaastrolib/1.0.0/> exists.
- [ ] `pip install mayaastrolib==1.0.0` in a scratch venv and compute a chart.
- [ ] Enable the ReadTheDocs project (see the section above) if not already.
