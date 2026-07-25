# Ruff Debt

Rules currently disabled in `pyproject.toml [tool.ruff.lint] ignore` and the reason for deferral.

## Pinned tooling versions

**Pinned in:** pyproject.toml `dev` extras on 2026-07-25 (Task v1.0-01)
**Versions:** `ruff==0.15.16`, `mypy==2.1.0`

`ruff format` output and mypy's error set both change between releases. With
floating `"ruff"` / `"mypy"` in the dev extras, "the pre-completion checklist
passes" was only true against whichever version the maintainer happened to have
— a fresh `pip install -e ".[dev]"` could pull a newer ruff that reports the
tree as unformatted, or a newer mypy that reports errors, on code that was
clean at the last commit. Both are dev-only tools, so pinning them does not
constrain library consumers.

The tree was re-settled with the pinned ruff when the pin landed: `ruff format .`
reported **131 files left unchanged**, i.e. zero churn — the formatting was
already consistent with 0.15.16, so no separate mechanical style commit was
needed. Bump the pins deliberately (as their own commit, with any resulting
format churn isolated), not incidentally.

## UP031 — printf-string-formatting

**Disabled in:** pyproject.toml on 2026-05-07 (Task 003)
**Reason:** 23 instances across `flatlib/` and `recipes/`, all using
`"%s ..." % var` style. Each one is functionally correct; the rule
asks for f-strings or `.format()`. Volume exceeds Task 003's
"~10 instances" hand-fix threshold, and several occurrences are in
recipe scripts that double as user-facing tutorials, where rewriting
percent-format would be a stylistic preference rather than a bug fix.
**Plan:** Resolve in a dedicated pyupgrade sweep (likely combined
with the camelCase → snake_case major-version cleanup, since both
involve touching every public-API file). Until then, percent-format
is allowed throughout the repo.
