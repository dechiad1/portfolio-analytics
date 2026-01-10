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
- PostgreSQL 14+
- Poetry

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set up PostgreSQL database:
```bash
createdb portfolio_users
```

3. Configure environment:
```bash
export APP_ENV=local  # or dev, prod
```

4. Run the server:
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
