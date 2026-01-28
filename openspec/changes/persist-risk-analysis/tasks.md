# Tasks: Persist Risk Analysis

## Epic: Persist Risk Analysis

Full specs and design: `openspec/changes/persist-risk-analysis/`

### Feature 1: Backend Data Layer

**Scope:** Database migration, domain model, repository port, and Postgres adapter

Create the foundation for storing risk analyses:
- Alembic migration for `risk_analysis` table with JSONB risks, FK to portfolio with CASCADE, indexes
- `RiskAnalysis` domain model in `api/domain/models/`
- `RiskAnalysisRepository` port interface in `api/domain/ports/`
- `PostgresRiskAnalysisRepository` adapter in `api/adapters/postgres/`

**Acceptance Criteria:**
- [ ] Migration creates table with id, portfolio_id, risks (JSONB), macro_climate_summary, model_used, created_at
- [ ] CASCADE delete removes analyses when portfolio deleted
- [ ] Repository implements create, get_by_id, get_by_portfolio_id, delete, get_portfolio_id_for_analysis
- [ ] Unit tests pass for repository

**Deliverable:** Repository can create, read, list, and delete risk analyses.

---

### Feature 2: Backend Service & API

**Scope:** Service modifications, dependency injection, all API endpoints

**Depends on:** Feature 1

Wire persistence into the application:
- Update `RiskAnalysisService` to accept repository, persist after LLM call, add get/list/delete methods
- Wire repository in `api/dependencies.py`
- Add/modify endpoints: POST (return id), GET list, GET by id, DELETE
- Update response schemas

**Acceptance Criteria:**
- [ ] POST /portfolios/{id}/risk-analysis saves result and returns id
- [ ] GET /portfolios/{id}/risk-analyses returns list ordered by created_at desc
- [ ] GET /portfolios/{id}/risk-analyses/{analysis_id} returns full analysis
- [ ] DELETE /portfolios/{id}/risk-analyses/{analysis_id} removes analysis
- [ ] 404 returned for non-existent analysis
- [ ] 403 returned when user lacks access to portfolio

**Deliverable:** Full API for persisted risk analyses.

---

### Feature 3: Frontend Integration

**Scope:** API client, state management, UI components

**Depends on:** Feature 2

Enable users to view and manage saved analyses:
- Add API functions for list/get/delete
- Update state to load latest analysis on mount, track current analysis id
- Update `RiskAnalysisSection` with history dropdown to view past analyses

**Acceptance Criteria:**
- [ ] Latest analysis loads automatically when viewing portfolio detail
- [ ] User can view list of historical analyses
- [ ] User can switch between past analyses
- [ ] Generating new analysis adds to history

**Deliverable:** Users can generate, view history, and switch between saved analyses.

---

### Feature 4: Testing

**Scope:** Unit tests for new backend code

**Depends on:** Feature 2

- Service tests for persistence logic and new methods
- Repository tests for CRUD operations

**Acceptance Criteria:**
- [ ] RiskAnalysisService tests cover persist-on-generate, get, list, delete
- [ ] PostgresRiskAnalysisRepository tests cover all CRUD operations
- [ ] All tests pass in CI

**Deliverable:** Test coverage for new functionality.
