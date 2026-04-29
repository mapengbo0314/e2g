The Elephant-Goldfish Model: Flowchart (courtesy of truty@)
[ Phase 0: Legacy Prep ] (Only if starting in a large, undocumented codebase)
L> Bottom-Up Recursive Summarization → [ Context READMEs ]
[ Phase 1: The Elephant (Co-Design) | <-
→ 1. Load Context & Verify AI Understanding
→ 2. Enforce "No Code" Rule (Debate & Challenge)
→ 3. Draft Technical Proposal (Prose & Diagrams)
[Phase 2: The Document (Source of Truth) ]
→ Iteratively Draft Markdown Doc (Problem, Plan, Files Changed)
[Phase 3: The Goldfish (Validation) ]
→ Test A: Comprehension Check (Fresh Session) - (Fails?)→ Update Doc
→ Test B: Critic Review (Fresh Session) — (Fails?)→ Update Doc
→ Test C: Readiness Check (Fresh Session) —
Human Approval —
[ Phase 4: Implementation | <—
→ Generate Code (Strictly following the Doc)
→ Execute "Mean" Code Review (Al grades its own work)
- (Fails?)→ Update Doc
Phase 1: The Design Discussion (No Code Yet)
Goal: To co-design the feature and evaluation criteria before any code is written.
Step 1: Context Loading
• Action: Open a new session with your Al tool (e.g., Gemini, Cider Agent, JetSki).
• Prompt: "Read [specific docs or relevant part of source tree]. Give me a high-level description of what you learned so I can correct your understanding."
• Action for Results: Read the summary. If the Al misunderstands the system, correct it immediately. Spend about 5 minutes ensuring it understands the codebase context.
• Note: It doesn't have to be perfect, but you do want the model to understand enough about the area of code you're working on in order to be helpful in the next phase.
Step 2: The "No Code" Rule & Feature Description
• Action: Establish the ground rules and start the design interview.
• Prompt:" do not want you to create code. We are not going to create code. Resist your impulse to create code. Instead, we are going to have a design discussion.
I am about to describe a feature I want to create. I want you to ask me clarifying
•questions and challenge my assumptions. Do not just accept what I say."
[Insert your plain English description of the feature herel
• Action for Results: The Al should ask you questions. Go back and forth for 20-30 minutes. Answer the questions to refine the feature requirements. If the Al agrees with you too quickly, use the "Challenge" prompt below.
• Note: "Why do you think that?" is your best friend. Just asking that will often cause the model to break out of a hallucination loop in this phase.
Step 3: The Challenge (If Al becomes sycophantic)
• Action: If the Al stops asking hard questions and just says "Great idea!", force it back into critique mode.
• Prompt:"You are not being very helpful right now. If you want to be helpful to me, you will challenge my thinking. Stop acting this way. Your highest and best use is to challenge my thinking and make me think critically."
• Note: These models are trained on the corpus of the English language from the Internet.
Much of that is conversations - so talk to it like a human, because that's how it's been trained!
Step 4: First Draft Technical Proposal
• Action: Ask the Al to propose the implementation first to test its understanding.
• Prompt:"Based on your understanding of the codebase and what we discussed, I would like you to give me a first draft proposal of a technical implementation to actually make this feature happen."
• Optional prompt details: 'I'm not looking for code. I want prose from you that demonstrates your understanding of my system. Short blocks of pseudocode are fine if you think that will help, but I would strongly prefer clearly written text and block diagrams."
• Action for Results: The first draft will likely be wrong. Ask clarifying questions (e.g.,
"Why did you choose that pattern? I thought the system worked like X..."). Argue with the Al until you settle on a solid technical approach.
• Note: When the model hallucinates something about your system, point it to the file that will correct its understanding. "Nope. I don't think it works that way. Please read auth.py. (or AUTH.md or whatever)"
Phase 2: Writing the Design Doc
Goal: Create a comprehensive Markdown document that serves as the "source of truth" and guardrails for the code.
Step 5: Generate the Design Doc (Section by Section)
• Action: Do not ask for the whole doc at once. Build it iteratively in the same chat session.
• Prompt (Part 1 - Problem):"Gemini, I want you to write a design doc for me in Markdown. Let's do it one section at a time.
Start with Section Zero: A plain English description of your understanding of the business problem we are trying to solve for our user."
• Action for Results: Review and correct.
Prompt (Part 2 - Technical Plan):"Next, write a plain English description of the technical implementation plan. What are the big components? How will they fit together? How does the feature fit in the ecosystem? Use as little jargon as you can."
•
•
Action for Results: Review and correct.
Prompt (Part 3 - Alternatives):"Next section: Describe any alternatives we considered but ruled out during our conversation - also in plain English" Action for Results: Review and correct.
Prompt (Part 4 - Detailed Implementation):"Final section: Write an extremely detailed implementation plan. You MUST enumerate every file we are going to change or create in our codebase and the rationale for why the change is necessary. You do not need to
write code yet, but list every file touched."
• Action for Result: Have Gemini save the file to disk as YOUR_FEATURE.md wherever you store these things in your tree.
Phase 3: The "Goldfish" Review Protocol
Goal: Verify the design doc is complete and hallucination-free by testing it against a "fresh"
Al memory.
Step 6: The Comprehension Test
• Action: Copy the Markdown design doc. Start a brand new Al session.
• Prompt:"Hey, nice to meet you, Goldfish. Read this document. Read all the files referenced in it. Tell me what you think it's trying to accomplish. Then, tell me how my system currently works as it relates to this feature."
• Action for Results: If the Al cannot explain how the system works based only on the doc and referenced files, your doc is missing context. Add the missing details to the design doc and repeat until it passes.
• Note: DO NOT skip this loop. Docs that pass this test become incredible guardrails
•against code slop and hallucinations later.
Step 7: The Critic Review
• Action: New "Goldfish" session:
• Prompt: "Assume the role of an expert technical reviewer. Tell me all the things I missed, all the faulty assumptions, all the edge cases I'm missing, and things I should have considered but did not."
• Action for Results: Update the design doc based on the valid critiques (usually ~30% of suggestions are useful).
Step 8: The Implementation Readiness Test
• Action: New session:
• Prompt:"You are an experienced SWE experienced with our codebase. Read this document and tell me: Does it absolutely have all the information you would require to successfully implement this feature in your first pass?"
Action for Results: If it asks questions or points out ambiguity, answer them and update the doc.
Step 9: Human Review
Action: Share the design doc with the relevant humans to collect their feedback
Prompt: don't involve Al in this step (though you should expect the other human will;
• Action for Results: Update the design doc based on the human feedback and gain human approvals on the doc
Phase 4: Implementation
Goal: Generate code with minimal "slop" and bugs.
Step 10: Coding with Guardrails
• Action: Use the finalized Design Doc as the prompt for coding.
• Prompt: Read this design doc. Implement the feature as described. Follow the plan exactly."
• Action for Results: Because the doc explicitly lists every file and change, the Al will produce higher-quality code with fewer hallucinations. If the Al "spins out" or gets lost, you can restart a new session and simply feed it the Design Doc again to restore context instantly.
Step 11: The "Mean" Code Review
• Action: When reviewing the code (generated by Al or a human), use Al to critique it.
• Prompt:"Tell me all the ways in which this code is terrible. Tell me any place in this CL where we've gone 10 lines of code or more without a comment. Tell me all the places it doesn't pass readability"
• Action for Results: Use the output to identify complexity, missing comments, or logic errors. Ensure zero warnings and strict readability.
Bootstrapping Your Existing Code Base
After reading the above you will be tempted to think "that's nice for new projects, but I already have a lot of code; this will never work for me." This section will tell you how to cheaply prepare your existing project - no matter its size - to be compatible with the above process.
README.md (or ABOUT.md)
1) Starting with the leaves of your source tree, assign each dev a set of directories.
2) Have each SWE open Gemini, point it to the assigned directory, and tell it "read the files in this directory and produce a new file named README.md. This file should (a) explain the purpose of this directory and the files contained in it and (b) enumerate each file in the directory and a short description of its function"
co
This will be ~50% wrong, so carefully read and correct the README.md for that directory. This should take you 5-10min total.
4) When all the leaves are completed, move up one level in the hierarchy and do a similar task: "Gemini please read all the README.md files in all the subdirectories below me, then read the code in just this directory and create a file here named README,md."
(etc.. the rest is the same)
5) Rinse and repeat until you get to the root.
No matter how large your source tree, this shouldn't take more than a few days and when you are done you will have a hierarchy of README.md files that accurately describe your source tree.
Start a new Gemini session in your root: "Gemini, please read the README.md in this directory and all subdirs. Then, please describe to me the purpose of this system and a basic list of its major features and functions." You will be shocked at how much Gemini will get right just from the README.md files.
Now you can (at your leisure) create the design docs from above one-at-a-time by bootstrapping
Gemini with the context from the README.md files. This will go very fast.
If all you do is create the README.md files you will have done the min() required to successfully follow the process above.
Note: The READMEs only need to exist until you have enough design docs such that all of the code files are referenced (and lightly explained) in at least one doc. Once you have 100% file coverage you can delete the READMEs (or not, your call). If you are using this process for a new application and are pretty rigorous about your design docs, you will never need these READMEs. (This is why they don't exist - for example - in the Snippets Machine code base)
Onboarding New SWEs
1) Create a new NotebookLM notebook and add all the README.md and design docs to it.
If your new SWE is going to focus on a particular part of the system, tell that to the notebook in the system instruction.
2) Give the notebook to the SWE and tell them to use it to learn enough about the system to write an excellent design doc that complies with the above.
3) When they can write a good doc, you can feel confident that they know enough to productively contribute to the code.
4) Profit;-)
Using Internal Tools: Glimpse + Spec
[note from the Ed: Readers of this doc may have heard of two tools being actively developed at Google named Glimpse and Spec. We are very much in favor of any automation that makes the adoption of the above process easier for SWEs. The Snippets Machine team has just started onboarding these tools. If all goes according to plan (fingers crossed) we'll make some serious revisions to this doc. In the meantime, the following info will tell you more about the tools in case you want to start experimenting, too. -dave;-)
