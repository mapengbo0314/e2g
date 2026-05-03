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
