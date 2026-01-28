# Risk Analysis History

## ADDED Requirements

### Requirement: List Historical Analyses

Users can view all past risk analyses for a portfolio.

#### Scenario: Portfolio has saved analyses

- **WHEN** a user requests the risk analysis history for a portfolio
- **AND** the portfolio has one or more saved analyses
- **THEN** the system returns a list of analyses ordered by creation date (newest first)
- **AND** each item includes id, timestamp, model_used, and risk count summary

#### Scenario: Portfolio has no saved analyses

- **WHEN** a user requests the risk analysis history for a portfolio
- **AND** the portfolio has no saved analyses
- **THEN** the system returns an empty list
