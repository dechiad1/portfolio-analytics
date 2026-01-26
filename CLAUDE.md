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

This project uses [Beads](https://github.com/steveyegge/beads) for issue tracking. See `.beads/README.md` for basic commands.

**Important:** Do not store sensitive information (passwords, API keys) in issue descriptions.

### Workflow

Always work on feature branches, not main. Commit code and `.beads/` together so issue state stays in sync.

```bash
git checkout -b feature/my-feature
bd update <id> --status in_progress
# ... make changes ...
git add <files> .beads/
bd sync
git commit -m "..."
git push
```

### Session Completion

Work is NOT done until `git push` succeeds.

1. File issues for remaining work (`bd create`)
2. Run quality gates if code changed (`task test:unit`)
3. Close completed issues (`bd close <id>`)
4. Commit and push
5. Verify `git status` shows clean working tree
