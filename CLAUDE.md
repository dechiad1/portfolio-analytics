# Portfolio Analytics

A monorepo for viewing and analyzing investment portfolios.

## Project Structure

| Directory | Stack | Purpose |
|-----------|-------|---------|
| `api/` | Python, FastAPI, Postgres | Transactional backend |
| `portfolio_analytics/` | dbt, DuckDB | OLAP data pipeline |
| `web/` | React, TypeScript | Frontend application |
| `docker/` | Docker Compose | Local infrastructure |

## Domain Concepts

**Security** - A tradeable instrument (stock, ETF, bond, cash). The registry supports multiple identifier types (ticker, CUSIP, ISIN) via `security_identifier` table. Equities and bonds have separate detail tables. Securities are shared across all users.

**Portfolio** - A named collection of holdings belonging to a user. Can be created empty, randomly generated, or via "dictation" (parsing text descriptions). Current state lives in `position_current`; history is append-only in `transaction_ledger`.

**Holding** - A position in a security within a portfolio. Links portfolio to security with quantity, cost basis, and current value. Creating holdings auto-creates missing securities in the registry.

**Simulation** - Monte Carlo projection of a portfolio's future value. Configurable by model type (gaussian, student-t, regime-switching), time horizon, and scenario overlays (e.g., Japan lost decade, stagflation). Results stored as JSONB.

## Architecture

The API follows hexagonal architecture. See `.claude/reference/hexagonal-architecture.md` for full details.

## Conventions
- Use `task <command>` (Taskfile) for tests, builds, and other dev commands
- Use `bd` (beads) for issue tracking. See `AGENTS.md` for workflow details.

## Issue Tracking (beads)

Do not store sensitive information (passwords, API keys, secrets) in issue descriptions or metadata.

```bash
bd ready              # Find available work
bd create "Title"     # Create an issue
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

### Git + Beads Workflow

Always work on feature branches, not main. Commit code and `.beads/` together so issue state stays in sync with code changes.

**Starting work:**
```bash
git checkout -b feature/my-feature
bd update <id> --status in_progress
```

**Committing changes:**
```bash
# 1. Stage code AND beads together
git add <changed-files> .beads/

# 2. Sync beads (exports issue state to .beads/issues.jsonl)
bd sync

# 3. Commit everything together
git commit -m "Description of changes"

# 4. Push
git push -u origin feature/my-feature
```

### Session Completion

Work is NOT done until `git push` succeeds.

1. File issues for remaining work (`bd create`)
2. Run quality gates if code changed (`task test:unit`)
3. Close completed issues (`bd close <id>`)
4. Commit and push:
   ```bash
   git add <files> .beads/
   bd sync
   git commit -m "..."
   git push
   ```
5. Verify `git status` shows clean working tree
