---
name: openspec-create-beads
description: Port a fully-documented OpenSpec change into beads epics and features for work tracking. Use before implementation to create trackable work items.
license: MIT
compatibility: Requires openspec CLI and bd (beads) CLI.
metadata:
  author: local
  version: "1.0"
---

Port an OpenSpec change into beads for pre-implementation work tracking.

**Input**: Change name is required. If omitted, prompt the user to provide it.

**Mapping**:
| OpenSpec | Beads |
|----------|-------|
| Change | Epic |
| Feature (from tasks.md) | Feature (parent=epic) |
| Acceptance criteria | Part of feature description |
| "Depends on: Feature N" | bd dep add |

**Steps**

1. **Get change name**

   If no argument provided, use **AskUserQuestion** to prompt:
   - Run `openspec list --json` to get available changes
   - Present options to user
   - Do NOT auto-select even if only one exists

   Always announce: "Porting change: <name> to beads"

2. **Validate the change exists and has tasks**

   ```bash
   openspec status --change "<name>" --json
   ```

   Check that:
   - Change exists
   - Has a `tasks.md` file (required for this skill)

   If missing tasks.md: "This change has no tasks.md file. Use /openspec-continue-change to create one first."

3. **Check for duplicate epic**

   ```bash
   bd search "<epic-title>" --type=epic --json
   ```

   If an epic with matching title exists:
   - Warn: "Epic '<title>' already exists (ID: <id>). This may be a duplicate import."
   - Use **AskUserQuestion** with options:
     - "Create anyway" - proceed with creation
     - "Cancel" - abort the operation
     - "Show existing" - run `bd show <id>` and stop

4. **Read and parse tasks.md**

   Read `openspec/changes/<name>/tasks.md` and extract:
   - Epic title (from `## Epic: <title>` heading)
   - Features (from `### Feature N: <title>` sections)
   - For each feature:
     - Scope (paragraph after title)
     - Dependencies (from `**Depends on:** Feature N` lines)
     - Acceptance criteria (from `**Acceptance Criteria:**` section, checkboxes)
     - Deliverable summary

5. **Read proposal for epic description**

   Read `openspec/changes/<name>/proposal.md` and extract:
   - The "Why" section for context

6. **Create the epic**

   ```bash
   bd create --type=epic --title="<epic-title>" --description="<description>" --silent
   ```

   Description format:
   ```
   <Why summary from proposal - 1-2 sentences>

   **OpenSpec Change:** openspec/changes/<name>/

   See proposal.md for full context and design.md for technical details.
   ```

   Capture the epic ID from output.

7. **Create features**

   For each feature in order:

   ```bash
   bd create --type=feature --parent=<epic-id> --title="<feature-title>" --description="<description>" --silent
   ```

   Description format:
   ```
   **Scope:** <scope paragraph from tasks.md>

   **Acceptance Criteria:**
   - [ ] Criterion 1
   - [ ] Criterion 2
   ...

   **Deliverable:** <deliverable summary>

   **Ref:** openspec/changes/<name>/tasks.md
   ```

   Track feature IDs mapped to feature numbers (Feature 1 -> bd-xxx, Feature 2 -> bd-yyy).

8. **Add dependencies between features**

   For each feature that has "Depends on: Feature N":

   ```bash
   bd dep add <this-feature-id> <depends-on-feature-id>
   ```

   This means: this feature is blocked by the feature it depends on.

9. **Show summary**

   Display:
   ```
   ## Beads Created from OpenSpec Change

   **Change:** <name>
   **Epic:** <epic-id> - <epic-title>

   **Features:**
   - <feature-1-id>: <title>
   - <feature-2-id>: <title> (blocked by <feature-1-id>)
   - <feature-3-id>: <title> (blocked by <feature-2-id>)
   ...

   Run `bd show <epic-id>` to see full epic details.
   Run `bd ready` to see which features are ready to work on.
   ```

**Output Example**

```
## Beads Created from OpenSpec Change

**Change:** persist-risk-analysis
**Epic:** bd-a1b2c3 - Persist Risk Analysis

**Features:**
- bd-d4e5f6: Backend Data Layer
- bd-g7h8i9: Backend Service & API (blocked by bd-d4e5f6)
- bd-j0k1l2: Frontend Integration (blocked by bd-g7h8i9)
- bd-m3n4o5: Testing (blocked by bd-g7h8i9)

Run `bd show bd-a1b2c3` to see full epic details.
Run `bd ready` to see which features are ready to work on.
```

**Guardrails**
- Always require change name (prompt if missing)
- Always check for duplicate epics before creating
- Parse tasks.md structure carefully - features may have varying formats
- Keep descriptions concise - link to OpenSpec artifacts for full details
- Do not duplicate content that is well-documented in OpenSpec
- Features are created as open (pending) for pre-implementation tracking
- Preserve dependency order: if Feature 2 depends on Feature 1, Feature 2 is blocked by Feature 1

**Error Handling**
- No tasks.md: suggest using openspec-continue-change first
- Invalid change name: list available changes
- bd command fails: show error, do not continue with partial creation
- Missing dependency reference: warn but continue (e.g., "Feature 99" referenced but doesn't exist)
