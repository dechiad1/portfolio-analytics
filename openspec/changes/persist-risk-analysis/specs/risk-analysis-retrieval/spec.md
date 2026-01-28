# Risk Analysis Retrieval

## ADDED Requirements

### Requirement: Retrieve Specific Analysis

Users can fetch the full details of a previously saved analysis.

#### Scenario: Analysis exists

- **WHEN** a user requests a specific analysis by ID
- **AND** the analysis exists and belongs to a portfolio the user can access
- **THEN** the system returns the full analysis including all risks and macro summary

#### Scenario: Analysis does not exist

- **WHEN** a user requests a specific analysis by ID
- **AND** no analysis exists with that ID
- **THEN** the system returns a 404 error

#### Scenario: User lacks access

- **WHEN** a user requests a specific analysis by ID
- **AND** the analysis belongs to another user's portfolio
- **AND** the requesting user is not an admin
- **THEN** the system returns a 403 error
