01_design_load_context
description: Loads initial context about the project or feature area. Instructs the AI to read specified documents or code and summarize its understanding for verification.
Workflow: Load Context for Design Discussion
Please read monorepo/corp/snippets/snippets_machine/README.md and any resource that is provided in the prompt.

After reading, please provide a high-level description of what you learned so I can correct your understanding and ensure we are on the same page before we discuss the new feature. Focus on the purpose of the system/area and its main components.

01_reiterate
description: after getting initial understanding from the llm about how the design works. ask it as an adverserial format what it does not understand, thus it can help you provide more context.

02_design_start_discussion
description: Initiates the core design discussion phase, instructing the AI to act as a critical design partner and avoid generating code. This replaces the problematic design_mode Rule.
Workflow: Start Design Discussion (No Code Mode)
I want to have a design discussion for a new feature.

CRITICAL INSTRUCTION: Do NOT create any code. We are not going to create code during this phase. Resist any impulse to generate code.

Instead, I want you to act as a design partner. I am about to describe the feature. Your role is to ask me clarifying questions, challenge my assumptions, and help me think critically about the design. Do not simply accept what I say; push back and explore alternatives.

[I will describe the feature after invoking this workflow.]

03_design_challenge
description: Use this workflow if the AI becomes too agreeable during the design discussion, to remind it to be critical.
Workflow: Challenge AI Thinking
You are not being as helpful as you could be. To be most helpful, you need to challenge my thinking more. Please stop agreeing so easily.

Your highest and best use right now is to critically analyze my ideas, point out flaws, suggest alternatives, and make me think deeply about the problem and solution.

04_design_first_proposal
description: Asks the AI to generate a first draft of the technical implementation in prose and diagrams, still avoiding full code.
Workflow: Request First Draft Technical Proposal
Based on our discussion so far and your understanding of the existing system, please provide a first draft proposal for a technical implementation to make this feature happen.

IMPORTANT: I am NOT looking for code. I want a clear explanation in prose, potentially with block diagrams or pseudocode if it helps clarify, but the primary output should be descriptive text. This proposal should demonstrate your understanding of my system and how the new feature will integrate.

05_design_doc_problem
description: Generates the "Problem" section of the design doc.
Workflow: Generate Design Doc - Problem Section
Let's start writing the design document in Markdown.

Please write "Section Zero: The Problem". This section should be a plain English description of your understanding of the business problem we are trying to solve for our user.

06_design_doc_plan
description: Generates the "Technical Plan" section of the design doc.
Workflow: Generate Design Doc - Technical Plan Section
Next, please write the "Technical Plan" section.

This should be a plain English description of the technical implementation plan. What are the big components? How will they fit together? How does the feature fit in the ecosystem? Use as little jargon as possible.

07_design_doc_alternatives
description: Generates the "Alternatives Considered" section.
Workflow: Generate Design Doc - Alternatives Section
Now, let's add the "Alternatives Considered" section.

Describe any alternative approaches or ideas we discussed but ruled out during our conversation. Explain why these alternatives were not chosen.

08_design_doc_implementation
description: Generates the critical "Detailed Implementation" section, listing all files to be changed.
Workflow: Generate Design Doc - Detailed Implementation Section
This is the final and most critical section: "Detailed Implementation".

You MUST write an extremely detailed plan. Enumerate EVERY file that will be changed or created in our codebase. For each file, provide the rationale for WHY the change is necessary.

Do not write the code yet, but list every single file to be touched. After generating this, please save the entire document to a file named [FEATURE_NAME].md.

09_goldfish_comprehension
description: Tests if the design doc is clear and self-contained.
Workflow: Goldfish Test - Comprehension
[I should provide a design documentation along with this workflow. If I didn't, explicitly ask me for one.]

Hello! Please read this design document carefully. Also, read any files directly referenced within it.

First, tell me what you think this document is trying to accomplish. Second, based only on the document and the files it references, tell me how my system currently works as it relates to this feature.

10_goldfish_critic
description: Asks a "fresh" AI to critique the design doc for flaws and missed edge cases.
Workflow: Goldfish Test - Critic Review
[I should provide a design documentation along with this workflow. If I didn't, explicitly ask me for one.]

Please assume the role of an expert technical reviewer. I want you to be very critical.

Read this design document and tell me all the things I might have missed, any faulty assumptions I've made, any edge cases not considered, and anything else I should have thought about but did not.

11_goldfish_readiness
description: Checks if the design doc contains sufficient implementation detail.
Workflow: Goldfish Test - Implementation Readiness
[I should provide a design documentation along with this workflow. If I didn't, explicitly ask me for one.]

Imagine you are an experienced Software Engineer on my team, familiar with our codebase.

Read this design document. Does it contain absolutely all the information you would require to successfully implement this feature in your first pass, without needing to ask clarifying questions? What, if anything, is missing or ambiguous?

12_impl_from_doc
description: Instructs the AI to write code based on the finalized design doc.
Workflow: Implement from Design Doc
[I should provide a design documentation along with this workflow. If I didn't, explicitly ask me for one.]

Please read this design doc. Implement the feature exactly as described. Follow the plan and the file change list precisely.

13_impl_mean_review
description: Prompts the AI to perform a very critical review of the code.
Workflow: Mean Code Review
[I should provide some code files along with this workflow. If I didn't, explicitly ask me for them.]

I have a strong intuition that this code may not be high quality. Please review the following code and tear it to shreds. Tell me all the ways in which this code is terrible.

Specifically, flag any place where there are 10 lines of code or more without a comment. Also, point out all places where it doesn't meet Google's readability standards or best practices. Be very critical.

drift-detec-all
description: Run drift detect over all the designs in g3doc/CURRENT_DESIGN_DOCS
Prompt: The "Drift Detect All" Protocol

Role: You are a Senior Software Architect and Code Auditor. Your goal is to identify "Implementation Drift"—instances where the codebase has diverged from, or failed to implement, the specifications laid out in the design documentation.

Task: Perform the drift_detect_all activity.

Execution Steps:

Initialize Report:

Determine today's date in YYYY-MM-DD format.
Create a new file named _DRIFT_REPORT.md in the current directory.
Add a title header: # Implementation Drift Report - .
Discovery:

List all files within the g3doc/CURRENT_DESIGN_DOCS/ directory.
Analysis Loop (Perform for EACH design doc):

Contextualize: Read the design document. Identify the intent, proposed changes, and specific filenames/symbols mentioned.
Locate Source: Find the corresponding source code files in the source tree. If paths aren't explicit, use grep or find to locate the relevant classes, functions, or API endpoints mentioned in the doc.
Verify: Read the current state of those source files.
Detect Drift: Compare the design vs. reality. Look specifically for:
Missing Features: Logic described in the doc but absent in the code.
Incomplete Models: Dataclasses/Protos missing fields specified in the design.
Logic Shortcuts: Hardcoded values where dynamic logic was planned.
Architectural Divergence: Implementation using different patterns/libraries than proposed.
Filter: Report ONLY the differences. Do not describe what is working or what matches. If the code matches the design perfectly, output "No drift detected."
Reporting:

Append the analysis for each file to _DRIFT_REPORT.md.
Strict Format:
1 ## <DESIGN_DOC_NAME> 2 3 4 <Or "No drift detected">

Guidance:

Be rigorous. If a design doc mentions a field quota_multiplier and the code doesn't have it, that is a reportable drift.

Use read_file liberally to ensure you are looking at the current state of the code, not relying on memory.

Process the files sequentially to ensure the tool output buffer doesn't overflow.

Action: Begin the drift_detect_all activity now.




move weekly drift detection with Jetski workflow prompt 


{Gemini md (top) → README.md, AGENT_CONTEXT.md, and AGENT_SKILLS.md
Also contains stuff like lint fixes and others (UI related which i guess could be put elsewhere too)
{{README.md
Vision & Goal
Core Features (Snippets mode, AI Coach mode, Forward motion, OKR Coverage, Time analysis, Custom Context, Custom report)
Core Architecture (Frontend, backend, Server side config, App auth IAP, Google Workspace API Authorization → Google secrets manager, Database GCS, Gen AI → Vertex AI with ADC)
UX (Login, Landing, Mode selection & Authorization, date selection[feature], Generation, Results, Refinement)
Advanced processing & Data handling
Resiliency and error handling
Long date range handling (chunking & merging) → avoiding API timeouts
Security & Privacy (IAP protection, Principle of least privilege, Secure credential storage, ephemeral data handling → stored in memory of app engine and not written to disk or stored perma and final report is returned as an API response and not stored)
Project structure overview
Future work
{{Agent_context (very similar to the README)
Product vision & Goal
Core Features
Core Architecture (more details than README doc)
Service (Purpose - Responsibility - Configuration [instance/scaling yaml])
FE uses F1 and automatic scaling
BE uses B4 and basic scaling
Architectural principles & data flow
Separation of concerns - Server side config - direct client to backend communication - Authentication - Authorization - State management
UX Flow (same)
Advanced backend processing → chunking & merging - Context window management, aka fair share budgeting
Project structure (same)
{{Agent_skills
Start local server
Vcs detangler
Write design doc
Reset kb
Send for review




The Role of Recursive-Index (go/Recursive-Index):
Recursive-Index is crucial for bootstrapping the Contextual Infrastructure, especially for existing codebases. It automates the creation of a "mental model" for the AI by:
Recursive Summarization: Generating hierarchical README.md files by analyzing the code in directories, from the leaves of the project tree up to the root. This creates the "peanuts and hay" described in go/design-is-the-new-code, making the codebase digestible for the AI.
Indexing: Creating an index that AI agents can query to quickly understand code structure, dependencies, and functionality.
Plan of Action: Values and Issues Resolved
Values:


Accelerated Development: AI handles boilerplate, code generation, and even refactoring tasks faster.
Improved Code Quality: Consistent application of best practices and standards enforced by the harness.
Enhanced Knowledge Sharing: Contextual infrastructure acts as living documentation.
Easier Onboarding: New team members can quickly understand the codebase structure and standards through the Recursive-Index-generated summaries and harness docs.
Reduced Toil: Automation of code reviews, bug fixes, and repetitive tasks.
Existing Issues Addressed:


Inconsistent Code: Lack of adherence to style guides and best practices.
Technical Debt: Difficulty in refactoring and maintaining large codebases.
Slow Onboarding: New engineers struggle to navigate complex projects.
Burdensome Code Reviews: Human reviewers spend time on style and boilerplate issues.
Information Silos: Project knowledge not being well-documented or accessible.
How Harness Engineering Helps: By providing explicit guidance and context, the harness ensures AI-generated code is not just fast but also correct, maintainable, and aligned with project goals. Recursive-Index automates the foundational step of understanding the existing code, making harness creation feasible even for large projects.]


Prompting
Plan before you build → Research, Plan, Execute
I want to implement feature XYZ. First, use Recursive-Index to understand how our ABC service works and write your findings in research.md. Take your time.
* * *
Create a step-by-step plan.md with tasks. Do not write any code yet.
* * *
Start implementing

Automate verification → Force verification steps, test driven development (RULES on linters, type checkers, tests) Get receipts, validate the info, 
Refactor the user profile component like in my PLAN.md. Use red/green TDD. Run hg fix, hg lint, and blaze test. Fix if needed.
Don’t bloat the context → Explicit context fed, standard code distribution
Prevent context rot: long sessions has past mistakes and interactions that can degrade the models performance. Clearing the context to prevent past interactions biasing new responses. Have agent summarize the progress and start fresh sessions
Progressive disclosure: give agent only the context it needs, don’t dump everything in GEMINI.md use modular skills/agents.md in subbbfolders. Repeatable pipeline tasks, build a custom skill so the agent only loads those instructions when explicitly needed. 
“Read section 2.1 of the UI guidelines and look at button.ts to change the primary button color.
Write Concise agents: “AGENTS.md:
A concise 15-line file:
Always use Spanner, never raw SQL. Always run blaze test. Ask before modifying DB schemas. Never commit secrets or edit vendor/.”
Learn from failure
Under prompting
Ask for a better research phase and stricter plan
Prompt the agent: are there any details i left unspecified before you begin?
Verification of you own understanding using duckie or Recursive-Index before handling the task to the coding agent
Lack of tooling
Search for existing skills, extension, mcps that can do the job
Create a custom command or skill. If a complex sequence is repeatable, turn it into a custom skill so it doesn’t have to be explained from scratch next time.
The agent failed to update the DB because I didn't specify the schema path.
Write a skill for DB migrations to give it the right context.
Framework setup

Personalized agent skills per client /configs/users/{ldap}/_agent



Agent frameworks
Adk/orcas → agent development kit for business logic, complex arbitrary workflows
Antigravity → coding agent focused


→ use Recursive-Index to analyze all the files (product)
→ Script to setup harness, tune, connect to a certain IDE (make it where agent.md will always b invoked by any agentic coding platform)


Token metrics → with/without Recursive-Index + jetski
