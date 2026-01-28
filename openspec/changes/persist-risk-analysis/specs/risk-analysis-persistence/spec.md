# Risk Analysis Persistence

## ADDED Requirements

### Requirement: Automatic Persistence on Generation

When a risk analysis is generated, the system automatically saves it to the database.

#### Scenario: Successful analysis is persisted

- **WHEN** a user requests risk analysis for a portfolio
- **AND** the LLM successfully generates the analysis
- **THEN** the analysis is saved to the database with a unique ID
- **AND** the analysis is linked to the portfolio
- **AND** the response includes the persisted analysis ID

#### Scenario: Failed analysis is not persisted

- **WHEN** a user requests risk analysis for a portfolio
- **AND** the LLM fails or returns an error
- **THEN** no record is saved to the database
- **AND** an error response is returned to the user
