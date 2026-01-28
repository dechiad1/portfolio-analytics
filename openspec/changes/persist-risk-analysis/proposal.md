# Proposal: Persist Risk Analysis

## Why

Risk analysis results are currently ephemeral -- they're generated on-demand via LLM and returned directly to the frontend, but never persisted. Users lose their analysis when they navigate away or refresh, and there's no way to track how risk profiles change over time. Persisting results enables historical comparison, reduces redundant LLM calls, and lets users reference past analyses.

## What Changes

- New `risk_analysis` database table to store analysis results with JSONB for complex data
- New repository port and Postgres adapter following the simulation pattern
- Modified `RiskAnalysisService` to save results after generation
- New API endpoints to list and retrieve saved analyses
- Frontend updates to load saved analyses and show history

## Capabilities

### New Capabilities
- `risk-analysis-persistence`: Save risk analysis results to database with portfolio association
- `risk-analysis-history`: View historical risk analyses for a portfolio
- `risk-analysis-retrieval`: Fetch a specific saved analysis by ID

### Modified Capabilities
- `risk-analysis-generation`: After generating analysis, automatically persist it

## Impact

- `api/alembic/versions/` - New migration for `risk_analysis` table
- `api/domain/models/` - New `RiskAnalysis` domain model
- `api/domain/ports/` - New `RiskAnalysisRepository` port
- `api/adapters/postgres/` - New `PostgresRiskAnalysisRepository` adapter
- `api/domain/services/risk_analysis_service.py` - Add persistence after generation
- `api/api/routers/portfolios.py` - Add GET endpoints for analyses
- `api/api/schemas/` - Add response schemas for persisted analyses
- `web/src/pages/portfolios/` - Update to load/display saved analyses
