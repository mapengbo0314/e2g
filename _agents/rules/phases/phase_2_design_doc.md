# Phase 2: Writing the Design Doc

**Goal**: Create a comprehensive Markdown document that serves as the "source of truth" and guardrails for the code.

## Step 5: Generate the Design Doc (Section by Section)
**Roles**: `Architect`, `Technical Writer`.

Do not generate the whole doc at once. Build it iteratively in the same chat session.

### Section Zero: Business Problem
- **Prompt**: "Write a plain English description of your understanding of the business problem we are trying to solve for our user."
- **Review**: User reviews and corrects.

### Section One: Technical Plan
- **Prompt**: "Write a plain English description of the technical implementation plan. What are the big components? How will they fit together? How does the feature fit in the ecosystem? Use as little jargon as you can."
- **Review**: User reviews and corrects.

### Section Two: Alternatives
- **Prompt**: "Describe any alternatives we considered but ruled out during our conversation - also in plain English."
- **Review**: User reviews and corrects.

### Section Three: Detailed Implementation
- **Prompt**: "Write an extremely detailed implementation plan. You MUST enumerate every file we are going to change or create in our codebase and the rationale for why the change is necessary. List every file touched."
- **Action**: Save the file to disk as `designs/YOUR_FEATURE.md`.

### Section Four: Sphinch Marks (Readiness Assertions)

> **This section is MANDATORY.** The design doc is not complete without sphinch marks.

**What are sphinch marks?** Binary pass/fail assertions embedded directly in the
design document. They define the finite set of properties the spec must satisfy
before implementation can begin. They replace open-ended adversarial reviews with
a convergent, checkable readiness gate.

**Why?** Without sphinch marks, every Goldfish Protocol review finds different
issues based on the reviewer's attention. The review process never converges.
Sphinch marks make the review deterministic: verify each mark, fix failures, done.

**Prompt**: "Now add a Sphinch Marks section to the design doc. For each of the
following categories, write 3-6 binary (yes/no) assertions that an implementer
or reviewer can mechanically verify:"

| Category | What to Assert |
|:---------|:---------------|
| **Cross-Document Consistency** | Field names, types, and tool references match across all related docs |
| **Interface Accuracy** | Proposed code calls existing methods with correct signatures and public APIs |
| **State Machine Completeness** | Every node/state has defined transitions, bounded loops, no dead ends |
| **Failure Mode Coverage** | Every "what if X fails?" has a defined recovery path |
| **Dependency Declarations** | Every import is listed, versions are specified, platform constraints noted |

**Format:** Use HTML comments as anchors and checkboxes as marks:
```markdown
<!-- SPHINCH: Cross-Document Consistency -->
### SM-1: Cross-Document Consistency
- [ ] Field `foo` has the same type in architecture §X and design §Y
- [ ] Every tool in the bindings table has a schema definition
```

**Rules for sphinch marks:**
1. Each mark must be verifiable with a single read/grep/compare operation.
2. Marks are frozen at doc creation time — do NOT add new marks during review.
3. A mark can be `[x]` (pass), `[ ]` (not yet checked), or `🔵 DEFERRED` (not needed for MVP, with rationale).
4. The doc is implementation-ready when all non-deferred marks are `[x]`.

- **Review**: User reviews the sphinch marks for completeness.
- **Action**: Sphinch marks become the termination condition for Phase 3.
