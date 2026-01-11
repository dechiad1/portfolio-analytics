# Portfolio Analytics API

Backend API for the portfolio analytics platform built with FastAPI following hexagonal architecture.

## Architecture

```
api/
├── config/              # Environment-specific YAML configurations
├── api/                 # API layer (routers, schemas, mappers)
│   ├── routers/         # FastAPI route handlers
│   ├── schemas/         # Request/response Pydantic models
│   └── mappers/         # Domain <-> API model converters
├── domain/              # Core business logic (no external dependencies)
│   ├── models/          # Domain entities
│   ├── ports/           # Abstract interfaces (ABC)
│   ├── services/        # Business logic orchestration
│   └── commands/        # Complex operations
├── adapters/            # External integrations
│   ├── postgres/        # PostgreSQL repository implementations
│   └── duckdb/          # DuckDB analytics repository
├── dependencies.py      # Dependency injection configuration
└── main.py              # Application entry point
```

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or use Docker - recommended)
- Poetry

## Setup

### Option 1: Using Docker (Recommended)

1. Install dependencies:
```bash
poetry install
```

2. Start PostgreSQL container:
```bash
# From project root
task docker:up
```

3. Run database migrations:
```bash
task db:migrate
```

4. Configure environment:
```bash
export APP_ENV=local  # defaults to local
```

5. Run the server:
```bash
poetry run python main.py
```

Or with uvicorn directly:
```bash
poetry run uvicorn main:app --reload
```

## API Endpoints

### Sessions
- `POST /sessions` - Create a new session
- `GET /sessions/{session_id}` - Get session details

### Holdings
- `GET /holdings` - List holdings for session
- `POST /holdings` - Create a single holding
- `POST /holdings/upload` - Upload CSV to bulk create holdings
- `PUT /holdings/{holding_id}` - Update a holding
- `DELETE /holdings/{holding_id}` - Delete a holding

### Analytics
- `GET /analytics` - Get portfolio analytics for session

## Session Management

Session ID is passed via the `X-Session-ID` header or `session_id` query parameter.

## Configuration

Configuration files are located in `config/`:
- `local.yaml` - Local development
- `dev.yaml` - Development environment
- `prod.yaml` - Production environment

Set `APP_ENV` environment variable to select configuration.

## CSV Upload Format

The CSV file must include these columns:
- ticker
- name
- asset_class
- sector
- broker
- purchase_date (YYYY-MM-DD format)

Example:
```csv
ticker,name,asset_class,sector,broker,purchase_date
AAPL,Apple Inc,Equity,Technology,Fidelity,2023-01-15
VTI,Vanguard Total Stock Market ETF,ETF,Diversified,Vanguard,2023-02-20
```

## Database Migrations

This project uses Alembic for database schema management. Migration scripts are stored in `api/alembic/versions/`.

### Common Migration Tasks

Run pending migrations:
```bash
task db:migrate
```

Create a new migration:
```bash
task db:migrate:create MESSAGE="description_of_changes"
```

View migration history:
```bash
task db:migrate:history
```

View current migration version:
```bash
task db:migrate:current
```

Rollback last migration:
```bash
task db:migrate:downgrade
```

### Direct Alembic Commands

All tasks above use `task` from the root directory. You can also run alembic directly from the `api` directory:

```bash
cd api
poetry run alembic upgrade head
poetry run alembic revision -m "description"
poetry run alembic history
poetry run alembic current
poetry run alembic downgrade -1
```

## Development

Run linting:
```bash
poetry run ruff check .
```

Run type checking:
```bash
poetry run mypy .
```

Run tests:
```bash
poetry run pytest
```
