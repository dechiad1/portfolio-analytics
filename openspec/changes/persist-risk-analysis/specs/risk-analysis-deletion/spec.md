# Risk Analysis Deletion

## ADDED Requirements

### Requirement: Delete Analysis

Users can delete a saved risk analysis.

#### Scenario: Successful deletion

- **WHEN** a user requests to delete an analysis
- **AND** the user owns the portfolio or is an admin
- **THEN** the analysis is removed from the database
- **AND** a success response is returned

#### Scenario: Cascade on portfolio deletion

- **WHEN** a portfolio is deleted
- **THEN** all associated risk analyses are automatically deleted
