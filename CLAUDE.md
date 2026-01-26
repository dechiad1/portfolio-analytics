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
Do not store sensitive information (passwords, API keys, secrets) in issue descriptions or metadata
```bash
bd ready              # Find available work
bd create "Title"     # Create an issue
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

### Session Completion

When ending a work session, complete these steps. Work is NOT done until `git push` succeeds.

1. File issues for remaining work (`bd create`)
2. Run quality gates if code changed (`task test:unit`)
3. Update issue status - close finished, update in-progress
4. Push to remote:
   ```bash
   git pull --rebase && bd sync && git push
   ```
5. Verify `git status` shows "up to date with origin"
