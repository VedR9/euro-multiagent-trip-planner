# Evaluation Framework (Evals)

To measure the success and reliability of the Multi-Agent Travel Planner, we will use the following evaluation metrics (evals) across the different agent layers.

## 1. Profiler Agent Evals
**Goal:** Accurately map unstructured text to structured JSON.
- **Extraction Accuracy:** What percentage of explicit entities (destinations, budget numbers) are correctly captured in the Pydantic model?
- **Constraint Handling:** If a user implies a constraint (e.g., "I'm a student" -> budget constraint), does the LLM infer it properly?
- **Metric:** Execute 50 test prompts and diff the resulting JSON against a human-labeled ground truth JSON. Target: 95% accuracy on explicit entities.

## 2. Researcher & Logistics Agents Evals (Mock Data)
**Goal:** Generate realistic, parseable, and relevant mock data.
- **Schema Adherence:** Percentage of times the LLM outputs valid JSON that cleanly passes Pydantic validation without exceptions. Target: 99%.
- **Preference Alignment:** If the profile says "hates crowds," what percentage of generated attractions include attributes reflecting quiet/secluded nature?
- **Metric:** LLM-as-a-Judge. Have a separate LLM evaluate the output data array against the user's preferences on a scale of 1-10.

## 3. Reviewer Agent (Validation Loop) Evals
**Goal:** Ensure strict adherence to hard constraints (budget, time).
- **Budget Adherence Rate:** Percentage of final itineraries where the total calculated cost is less than or equal to the original budget constraint. Target: 100%.
- **Loop Efficiency:** The average number of rejection loops required before a valid itinerary is produced. Target: < 1.5 loops on average.
- **Metric:** Run 100 automated end-to-end tests with strict budgets. Track the pass/fail rate of the final output and the average loop count.

## 4. System End-to-End Evals
**Goal:** Produce a high-quality final product for the user.
- **Task Success Rate:** Did the system produce a final markdown itinerary that addresses the user's prompt without hitting the maximum loop retry limit?
- **End-to-End Latency:** Time taken from prompt submission to final itinerary generation. Target (Phase 1 using LLMs): < 20 seconds. 
- **Human Eval (Vibe Check):** Qualitative scoring by a human reviewer on how "good" and readable the final itinerary is.
