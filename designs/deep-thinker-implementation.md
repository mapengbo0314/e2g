# Deep Thinker Implementation Plan

## PR #1: Core Data Models and State Persistence

Goal: Establish the foundational data structures and the ability to save/load
the project's state.

This PR will not contain any active workflow logic.

### What's in this PR

- Implementation of the core Python classes: `ResearchProject`,
  `ResearchPlan`, `ResearchStep`, and `ResearchReport`.
- Methods for serializing a `ResearchProject` instance to a JSON string/file.
- Methods for deserializing a JSON string/file back into a
  `ResearchProject` instance.
- A basic `main.py` script with a test function that:
  - Creates a sample `ResearchProject` with a couple of dummy
    `ResearchStep` objects.
  - Saves the project to `research_project_state.json`.
  - Loads the project from the file into a new object.
  - Asserts that the loaded object is identical to the original.

### What's NOT in this PR

- Any agent or LLM interaction.
- The workflow execution loop.
- User input handling.

Result after this PR: A solid, testable foundation for the project's state
management.

## PR #2: The Workflow Orchestrator and Manual Execution Loop

Goal: Implement the main workflow engine that can run a pre-defined plan from
start to finish without any AI. This validates the state machine logic.

### What's in this PR

- A `WorkflowEngine` class that takes a `ResearchProject` as input.
- A `run()` method in the engine that iterates through the execution phases.

For this PR, the phases will be simplified:

- Phase 1-3 (Initialization, Planning, Review): Skips these and starts by
  loading a `research_project_state.json` file that is manually created by the
  developer for testing.
- Phase 4 (Execution Loop): The engine will loop through the `ResearchStep`
  objects in the plan. For each step, it will:
  - Print the step's description to the console (simulating "execution").
  - Update the step's status from `PENDING` to `COMPLETED`.
  - Save the project state to the JSON file after each step.
- Phase 5 (Finalization): Prints "Workflow Complete" to the console.

### What's NOT in this PR

- Agent interaction.
- Dynamic plan generation or modification.
- The interactive `y/n/m` user review.

Result after this PR: A runnable system that can execute a hard-coded research
plan, proving the core loop and state updates work correctly.

## PR #3: Agent-Powered Initial Planning

Goal: Integrate the AI agent for the first time to dynamically generate the
initial research plan.

### What's in this PR

- An `Agent` class responsible for all LLM interactions.
- Modification of the `WorkflowEngine` to implement Phase 1 and 2:
  - The `run()` method will now start by asking the user for a high-level
    research goal.
  - It will pass this goal to the `Agent`.
  - The `Agent` will perform the "foundational question" step and generate the
    initial `ResearchPlan` object.
  - The generated plan will be saved to the project state.

### What's NOT in this PR

- The `y/n/m` review flow.
- Agent-driven execution of steps (the loop from PR #2 will still just print
  the description).
- Plan adaptation.

Result after this PR: The system can now take a user's goal and, using an LLM,
automatically generate a structured research plan and save it.

## PR #4: Interactive User Approval Flow (`y/n/m`)

Goal: Implement the crucial user review and manual modification step.

### What's in this PR

- Updates to the `WorkflowEngine` to implement Phase 3 logic:
  - After the plan is generated (from PR #3), the engine will print the plan to
    the user.
  - It will prompt the user for `y/n/m` input.
  - It will implement the logic for each choice:
    - `y`: Continue to the execution loop.
    - `n`: Clear the current plan and loop back to the agent-planning phase.
    - `m`: Implement the logic to save the plan to `plan_for_edit.json`, wait
      for the user, and then load it back in.

### What's NOT in this PR

- Agent-driven execution or adaptation.

Result after this PR: A complete user-centric planning front-end. The user can
collaborate with the agent to produce a satisfactory plan before any execution
begins.

## PR #5: Agent-Driven Step Execution

Goal: Replace the placeholder execution logic with actual agent-driven research
for each step.

### What's in this PR

- Expansion of the `Agent` class with a method like
  `execute_research_step(step)`.
- Modification of the Phase 4 execution loop in `WorkflowEngine`:
  - Instead of just printing the step description, the engine will now call
    `agent.execute_research_step()`.
  - The agent will perform the required action (e.g. ask the `DEEP_QUESTION`).
  - The text result from the agent will be stored in `step.results` and added
    to the `ResearchReport`.
  - The project state will be saved after each successful step execution.

### What's NOT in this PR

- Dynamic plan adaptation during the loop.

Result after this PR: The system is now a fully functional, end-to-end
research tool that can execute a user-approved plan from start to finish.

## PR #6: Dynamic Plan Adaptation with Agent Tools

Goal: Implement the final and most advanced feature: allowing the agent to
modify the plan mid-execution.

### What's in this PR

- Implementation of the Plan Modification Interface functions:
  `add_step`, `remove_step`, `modify_step`.
- These functions will be exposed to the Agent as callable "tools".
- Modification of the execution loop (Phase 4d):
  - After a step is successfully executed, the `WorkflowEngine` will make a
    final call to the Agent.
  - This call will provide the agent with the results of the last step and
    prompt it to decide if the plan needs modification.
  - The agent's prompt will be engineered to instruct it to use the provided
    tools (`add_step`, etc.) if it determines a change is necessary.
  - Robust error handling in case the agent tries to use a tool incorrectly
    (e.g. modify a step that doesn't exist).

Result after this PR: The system is feature-complete. It is now a truly
"agentic" workflow that can not only execute a plan but also dynamically adapt
that plan in response to new information.
