# Ruff Debt

Rules currently disabled in `pyproject.toml [tool.ruff.lint] ignore` and the reason for deferral.

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
