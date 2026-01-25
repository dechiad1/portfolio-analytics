## Feature: Add the capability to build portfolios quickly & with a better user experience

Remember to read the content in CLAUDE.md, .claude/agents & .claude/reference FIRST to understand the coding conventions, desired repository structures & goal of the project

### Completion
In order to build this feature, please use the Taskfile. There are tasks for executing tests, for starting dev servers via overmind (for you to read logs) & you can use WebFetch to validate the application on its running ports. 

when all the tasks are fully complete & tested, print just DONEZO. 

DO NOT SKIP THIS STEP. IT IS REQUIRED WHEN FULLY COMPLETE

### Description
To build a portfolio today, we navigate to the portfolios page & click create portfolio. This creates an empty portfolio & then users have to manually add securities as holdings one at a time. I would like to add two new mechanisms to create a portfolio
1. existing: create an empty portfolio
2. new: create a portfolio with a random number of securities & allocation
3. new: allow the user to dictate a summary of their portfolio. The dictation, once converted to text, uses an llm to allocate securities based on the users description.

#### Changes to existing
The create portfolio button opens a modal that allows the user to select a name & a base currency. We want to add a third field that will drive this functionality - a single selection of either empty (current functionality), random or "tell us about your assets". 

#### Random
When the user selects the random option in the modal the only other thing they need to do is specify the total value of the portfolio. It should default to 100,000 in the base currency. Then the service will randomly alot securities from the security registry across asset classes to the new portfolio. 

#### Dictation
When the user selects the "tell us about your assets" the client should display a text box with a dictation option (client side must have microphone capabilities) where they will type a description of their portfolio. This description is sent to the BE service where we will build an llm integration (use ports & adapters hex arch) that will accept the description & select the approximate securities from the security registry to populate the portfolio. 

If the user's description is invalid (does not add up to 100% or we have nothing in the registry that matches), we share this information with the user in a tool tip that appears as the portfolio is created. We proceed to create the portfolio, filling in the missing with our best effort next match.

---

## Implementation Plan

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API Strategy | Extend existing POST /portfolios | Cleaner API, atomic creation |
| LLM Port | Add method to existing LLMRepository | Avoids port proliferation, similar patterns |
| Speech-to-Text | Web Speech API | No dependencies, native browser support, graceful fallback |
| Error Handling | Return matched + unmatched in response | User sees what worked, can fix manually |

---

### API Changes

#### Modified: POST /portfolios

```python
class CreatePortfolioRequest(BaseModel):
    name: str
    base_currency: str = "USD"
    creation_mode: Literal["empty", "random", "dictation"] = "empty"
    total_value: Decimal | None = None      # Required for random mode (default 100000)
    description: str | None = None           # Required for dictation mode
```

Response extended with:
```python
    holdings_created: int = 0
    unmatched_descriptions: list[str] = []  # Dictation mode only
```

#### New: GET /securities/registry

Returns all securities available for allocation (for frontend reference).

---

### Files to Create

#### Backend (6 new files)

| File | Purpose |
|------|---------|
| `api/domain/ports/security_registry_repository.py` | Port for querying security registry |
| `api/adapters/postgres/security_registry_repository.py` | Postgres implementation |
| `api/domain/services/portfolio_builder_service.py` | Orchestrates random/dictation portfolio creation |
| `api/domain/models/security.py` | Security domain model |
| `api/api/routers/securities.py` | Securities endpoints |
| `api/api/schemas/security.py` | Security schemas |

#### Frontend (3 new files)

| File | Purpose |
|------|---------|
| `web/src/pages/portfolios/components/CreationModeSelector.tsx` | Radio buttons for mode selection |
| `web/src/pages/portfolios/components/DictationInput.tsx` | Text/speech input component |
| `web/src/shared/hooks/useSpeechRecognition.ts` | Web Speech API wrapper |

---

### Files to Modify

#### Backend (6 files)

| File | Changes |
|------|---------|
| `api/api/schemas/portfolio.py` | Add mode fields to request, extend response |
| `api/api/routers/portfolios.py` | Handle creation modes, inject builder service |
| `api/domain/ports/llm_repository.py` | Add `interpret_portfolio_description` method |
| `api/adapters/llm/anthropic_repository.py` | Implement interpretation with structured prompt |
| `api/dependencies.py` | Add new singletons for registry and builder service |
| `api/main.py` | Include securities router |

#### Frontend (5 files)

| File | Changes |
|------|---------|
| `web/src/pages/portfolios/components/CreatePortfolioModal.tsx` | Add mode state, conditional fields |
| `web/src/pages/portfolios/portfolioApi.ts` | Extend createPortfolio, add fetchSecurityRegistry |
| `web/src/shared/types/index.ts` | Add CreationMode, PortfolioBuilderInput types |
| `web/src/pages/portfolios/usePortfolioListState.ts` | Handle extended input/response |
| `web/src/pages/portfolios/components/CreatePortfolioModal.module.css` | Styles for mode selector, dictation |

---

### Implementation Order

#### Phase 1: Listing all securities in the registry
1. The TickerRepository needs a method to list all securities: def get_all_securities(self) -> list[Security]
2. Implement in PostgresTickerRepository
3. Add GET /tickers/all endpoint

#### Phase 2: Random Mode
1. Create `PortfolioBuilderService` with random allocation logic
2. Extend portfolio schema with mode fields
3. Modify portfolios router to handle random mode
4. Tests for random generation

#### Phase 3: LLM Dictation Mode
1. Add `interpret_portfolio_description` to LLMRepository port
2. Implement in AnthropicLLMRepository
3. Add `build_from_description` to PortfolioBuilderService
4. Tests with mocked LLM
NOTE: when converting description to portfolio, the LLM needs access to the list of available securities & their metadata to perform mapping

#### Phase 4: Frontend Mode Selector
1. Create `CreationModeSelector` component
2. Update `CreatePortfolioModal` with mode switching
3. Add value input for random mode
4. Update API client and types

#### Phase 5: Frontend Dictation
1. Create `useSpeechRecognition` hook
2. Create `DictationInput` component
3. Integrate into modal
4. Browser compatibility fallback

#### Phase 6: Integration
1. End-to-end testing all modes
2. Error handling polish
3. Display unmatched descriptions
4. User feedback (tooltips, loading states)

---

### Random Allocation Logic

```python
def generate_random_allocation(securities, total_value):
    # Filter to ETFs and stocks
    eligible = [s for s in securities if s.asset_type in ('EQUITY', 'ETF')]

    # Select 5-15 securities randomly
    count = random.randint(5, min(15, len(eligible)))
    selected = random.sample(eligible, count)

    # Generate weights with minimum 2% per security
    weights = random.dirichlet distribution, normalized

    # Create holdings with calculated values
    return allocations
```

---

### LLM Interpretation Prompt (Summary)

- Provide full security registry as context
- Map user descriptions to specific tickers (e.g., "S&P 500" -> SPY/VOO)
- Return structured JSON with allocations + unmatched
- Allocations must sum to 100%

---

### Verification Plan

#### Unit Tests
- `test_portfolio_builder_service.py` - Random allocation logic
- `test_security_registry_repository.py` - Registry queries
- Mock LLM tests for interpretation

#### Integration Tests
- POST /portfolios with each mode
- Holdings created correctly
- Error responses for invalid inputs

#### Manual Testing
1. Create empty portfolio (regression)
2. Create random portfolio with default value
3. Create random portfolio with custom value
4. Create dictation portfolio with text input
5. Create dictation portfolio with speech input (Chrome)
6. Verify unmatched descriptions display
7. Test browser without Speech API support

#### E2E Test
- Add Playwright test for full modal flow with each mode

---

### Critical Files

Backend entry points:
- `api/api/routers/portfolios.py:77-94` - Create endpoint to modify
- `api/domain/ports/llm_repository.py` - Port to extend
- `api/dependencies.py` - DI wiring

Frontend entry points:
- `web/src/pages/portfolios/components/CreatePortfolioModal.tsx` - Modal to extend
- `web/src/pages/portfolios/usePortfolioListState.ts` - State hook to update
