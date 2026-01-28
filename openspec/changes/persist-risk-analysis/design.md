# Design: Persist Risk Analysis

## Context

The codebase follows hexagonal architecture with clear separation between domain (services, models, ports) and adapters (postgres, llm). Simulations already demonstrate the pattern for persisting complex LLM-generated results using JSONB columns. We'll follow this established pattern.

## Goals / Non-Goals

**Goals:**
- Persist risk analysis results following existing simulation pattern
- Enable historical comparison of risk analyses
- Maintain hexagonal architecture boundaries
- Support cascade deletion when portfolio is removed

**Non-Goals:**
- Diffing or comparing analyses (future feature)
- Scheduling automatic re-analysis (future feature)
- Storing raw LLM prompts/responses for debugging (out of scope)
- Frontend redesign of risk analysis UI (minimal changes only)

## Decisions

### Decision 1: Database Schema

Follow the simulation table pattern with JSONB for complex nested data:

```sql
CREATE TABLE risk_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
    risks JSONB NOT NULL,
    macro_climate_summary TEXT NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_analysis_portfolio_id ON risk_analysis(portfolio_id);
CREATE INDEX idx_risk_analysis_created_at ON risk_analysis(created_at DESC);
```

**Rationale:** JSONB for `risks` array allows flexible schema evolution without migrations. Matches simulation pattern. CASCADE delete handles cleanup automatically.

### Decision 2: Domain Model Location

Create `api/domain/models/risk_analysis.py` with a Pydantic model mirroring the existing `RiskAnalysis` dataclass from the LLM port, but adding `id` and `portfolio_id` fields.

**Rationale:** Keep domain models separate from port definitions. The port's `RiskAnalysis` is the LLM response shape; the domain model is the persisted entity.

### Decision 3: Repository Interface

Create `api/domain/ports/risk_analysis_repository.py`:

```python
class RiskAnalysisRepository(ABC):
    def create(self, analysis: RiskAnalysis) -> RiskAnalysis
    def get_by_id(self, id: UUID) -> RiskAnalysis | None
    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[RiskAnalysis]
    def delete(self, id: UUID) -> bool
    def get_portfolio_id_for_analysis(self, id: UUID) -> UUID | None
```

**Rationale:** Mirrors `SimulationRepository` interface. `get_portfolio_id_for_analysis` enables authorization checks without loading full analysis.

### Decision 4: Service Modification

Modify `RiskAnalysisService` to:
1. Accept `RiskAnalysisRepository` as constructor dependency
2. After successful LLM call, persist the result
3. Return the persisted model (with ID) instead of raw LLM response
4. Add methods: `get_analysis()`, `list_analyses()`, `delete_analysis()`

**Rationale:** Keeps persistence logic in domain layer. Service orchestrates LLM + persistence.

### Decision 5: API Endpoints

Add to portfolios router:
- `GET /portfolios/{id}/risk-analyses` - List analyses for portfolio
- `GET /portfolios/{id}/risk-analyses/{analysis_id}` - Get specific analysis
- `DELETE /portfolios/{id}/risk-analyses/{analysis_id}` - Delete analysis

Keep existing `POST /portfolios/{id}/risk-analysis` but modify response to include `id`.

**Rationale:** Nest under portfolios for clear ownership. Plural "analyses" for list endpoint follows REST conventions.

### Decision 6: Frontend Changes

Minimal changes:
1. On portfolio detail load, fetch latest analysis if exists
2. Add dropdown/list to view historical analyses
3. Update state to track `analysisId` for the current view
4. No major UI redesign

**Rationale:** Keep scope contained. UI improvements can come later.
