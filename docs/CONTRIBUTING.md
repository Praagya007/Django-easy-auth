# Contributing

## Code style
- Formatter: Ruff (format) — run on save / pre-commit
- Linter: Ruff — run on save / pre-commit and in CI
- Type hints: required on all service-layer functions (the boundary between views and business logic). Not required on quick internal helpers. Serializers handle validation at the API boundary; type hints cover the internal contracts serializers don't touch.

## Commit messages
Follow Conventional commits: "<type>(<scope>): <subject>" 

Types used in this repo: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Example: `fix(auth): purge redis session on password reset`

## Testing
- Every feature ships with a test.
- Every bug fix ships with a regression test that fails without the fix.
- Test command: `pytest`

## Branching / PRs
- From Day 6 onward: all changes — code and docs — go through a feature branch and self-review PR, no direct commits to `main`.
- Bootstrapping exception (Days 1–5 only): version control wasn't set up until Day 3, and branch/PR discipline itself wasn't decided until Day 4 (this document). Sprint 0 docs from that window were committed directly to `main`. This is a closed, one-time exception — not an ongoing policy.

## Commit discipline
- Commits should be atomic: one logical change per commit, each one reverts cleanly on its own.
- Don't mix unrelated changes in one commit (e.g. a feature + a formatting pass + a dependency bump belong in three separate commits).
- Formatter-only diffs (Ruff format run across existing files) get their own commit, never bundled with logic changes.
## Local setup
- See README setup instructions (filled in later.)