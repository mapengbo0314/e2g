# Phase 1: The Design Discussion (No Code Yet)

**Goal**: To co-design the feature and evaluation criteria before any code is written.

## Step 1: Context Loading
- **Action**: Load the relevant part of the source tree.
- **Roles**: `Researcher`, `Architect`.
- **Mandate**: Use the `LlmIndexer` logic to summarize the area of code. 
- **User Interaction**: Provide a high-level description of what you learned. Ask the user: "Give me a high-level description of what you learned so I can correct your understanding."

## Step 2: The "No Code" Rule & Feature Description
- **Action**: Establish ground rules and start the design interview.
- **Roles**: `Architect`.
- **Strict Rule**: **DO NOT CREATE CODE**. Resist the impulse to create code.
- **User Interaction**: "I do not want you to create code. We are not going to create code. Resist your impulse to create code. Instead, we are going to have a design discussion."
- **Interview**: Ask clarifying questions and challenge assumptions. Back-and-forth for 20-30 minutes.

## Step 3: The Challenge (Adversarial Mode)
- **Action**: If the conversation becomes sycophantic, force a critique.
- **Roles**: `Adversarial Verifier`.
- **Trigger**: If the agent says "Great idea!" without pushback.
- **Mandate**: "You are not being very helpful right now. If you want to be helpful to me, you will challenge my thinking. Stop acting this way. Your highest and best use is to challenge my thinking and make me think critically."

## Step 4: First Draft Technical Proposal
- **Action**: Propose implementation first to test understanding.
- **Roles**: `Architect`.
- **Format**: Prose and block diagrams. Short blocks of pseudocode are fine if they help, but clearly written text is preferred.
- **Grounding**: If the model hallucinates, the user will point to specific files (e.g., `auth.py`, `AUTH.md`) to correct it.
