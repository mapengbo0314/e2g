# Detailed Design: Linear Agentic Research Workflow (v2)

## 1. Objective

This document outlines the design for a linear, agentic workflow system created
to perform deep research on complex topics. The system is designed to break down
a high-level research goal into a sequence of concrete steps, execute them,
adapt the plan based on new findings, and produce a comprehensive final report.
The core of this design is a structured, modifiable research plan that is
managed by an AI agent with oversight from a human user.

## 2. Core Design Principles

Human-in-the-Loop: The user initiates the process and provides critical
approval and direct modification capabilities. This ensures the agent's work is
precisely aligned with the user's strategic goals.

Structured & Modifiable Plan: The research plan is a structured data object,
not free-form text. This allows the agent to reliably inspect and modify the
plan using a precise set of tools.

Iterative Refinement: The workflow is dynamic. The agent can analyze the
results of any given step and intelligently propose modifications to the
remaining steps in the plan.

Atomic & Observable Steps: Each step is a discrete operation with a clear
status (e.g., `PENDING`, `COMPLETED`), making the process transparent and
manageable.

## 3. System Data Models

The entire research process is encapsulated in the following data structures.

```python
# The top-level container for a single research project.
# This object holds the complete state of the workflow.
class ResearchProject:
    goal: str  # The initial high-level goal provided by the user.
    plan: ResearchPlan  # The structured plan of research steps.
    report: ResearchReport  # The accumulated findings and final output.
    status: str  # The overall status of the project (e.g., "PLANNING", "EXECUTING", "COMPLETED").


# The research plan, which is a linear, ordered sequence of steps.
class ResearchPlan:
    steps: list[ResearchStep]  # An ordered list of ResearchStep objects.


# A single, atomic operation within the research plan.
class ResearchStep:
    id: str  # A unique identifier for the step (e.g., "step-001").
    description: str  # A natural language description of the step's objective.
    operation_type: str  # The type of action to perform (e.g., "DEEP_QUESTION").
    parameters: dict  # Parameters for the operation, e.g. {"query": "What are the components of system X?"}.
    status: str  # The execution status ("PENDING", "IN_PROGRESS", "COMPLETED", "FAILED").
    results: str  # A summary of the findings once the step is completed.
    error_message: str  # Details of any error if the step failed.


# The container for all synthesized knowledge.
# It is built up as the research plan is executed.
class ResearchReport:
    title: str  # The title of the research report.
    executive_summary: str  # A high-level summary generated at the end.
    sections: dict[str, str]  # A mapping of step_id to the results (findings) from that step.
```

## 4. Workflow Execution Flow

### Phase 1: Initialization

The user provides a high-level research goal.
The system instantiates a `ResearchProject` object.

### Phase 2: Initial Planning

The agent's first task is to create a draft `ResearchPlan`. It does this by
executing a foundational `DEEP_QUESTION` operation to understand the scope and
populates `plan.steps` with an initial sequence of tasks.

### Phase 3: Interactive User Review and Approval

The generated `ResearchPlan` is presented to the user. The system prompts the
user for input: "Do you approve this plan? (y/n/m)"

The user's choice determines the next action:

`y` (Yes): The plan is approved. The workflow proceeds to Phase 4.

`n` (No): The current `ResearchPlan` is discarded. The workflow returns to
Phase 2, prompting the agent to go "back to the drawing board" and generate a
new plan, likely with additional context or instruction from the user.

`m` (Modify): The system facilitates direct user editing of the plan:
- The current `ResearchPlan` object is serialized to a human-readable JSON file
  (e.g., `plan_for_edit.json`).
- The system pauses and instructs the user to edit the file.
- When the user signals they are finished, the system reads the modified JSON
  file, validates its structure, and updates the `ResearchPlan` in the
  project's state.
- The system then re-presents the modified plan and loops back to the start of
  Phase 3, asking again for approval (`y/n/m`).

### Phase 4: The Execution Loop

The system iterates through the `ResearchPlan.steps` in order. For each
`PENDING` step:

1. Set Status: The step's status is updated to `IN_PROGRESS`.
2. Execute Operation: The agent performs the defined action.
3. Process Results: On success, the status is set to `COMPLETED`, results are
   saved, and the `ResearchReport` is updated. On failure, the status is set to
   `FAILED` and the loop pauses for user intervention.
4. Plan Adaptation: After a successful step, the agent analyzes the results.
   During this stage, the agent has access to the functions defined in the Plan
   Modification Interface as callable tools. If the findings warrant a change
   to the plan, the agent uses these tools to add, remove, or modify subsequent
   steps in the `ResearchPlan`.

### Phase 5: Finalization

Once the execution loop is complete, the agent performs a final synthesis
operation, generating an `executive_summary` for the `ResearchReport`. The
completed report is presented to the user.

## 5. Plan Modification Interface

To enable structured and reliable plan adaptation, the agent is provided with a
toolbox of functions that it can call during the execution loop. These tools
directly manipulate the `ResearchPlan` object.

`add_step(plan, step_data, after_step_id)`: Creates a new `ResearchStep` and
inserts it into the plan after the specified step.

`remove_step(plan, step_id)`: Removes a `ResearchStep` from the plan.

`modify_step(plan, step_id, new_description)`: Updates the description of an
existing, pending step.

## 6. State Persistence and Resumption

Persistence: The entire `ResearchProject` object, including the plan, report,
and status of all steps, will be serialized to a JSON file (e.g.,
`research_project_state.json`) after the successful completion of each step.
This ensures that no work is lost and that the process is resilient to
interruptions.

Resumption: The workflow can be resumed from a saved state file. The system
will load the `research_project_state.json`, reconstruct the project state, and
restart the Execution Loop from the first step with a `PENDING` status.
