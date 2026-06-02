# Edge Cases & Failure Modes

This document outlines potential edge cases and failure modes for the Multi-Agent Travel Planner, specifically mapped to our current Phase 1 (LLM Mock Data) implementation plan.

## 1. Profiling Agent Edge Cases
- **Missing Core Parameters:** The user provides a vague prompt (e.g., "Plan a trip for me" with no destination, budget, or timeline).
  - *Mitigation:* Profiler should set default fallback values (e.g., 3 days, $1000) or ideally, trigger the Orchestrator to ask the user a clarifying question.
- **Unrealistic Budget vs. Duration:** (e.g., "Plan a 14-day trip to Paris with a $50 budget.")
  - *Mitigation:* Profiler extracts it accurately, but the Reviewer Agent must catch this constraint failure and gracefully reject the itinerary early.
- **Conflicting Preferences:** (e.g., "I want extreme adventure and nightlife, but I hate loud places and need a relaxing trip.")
  - *Mitigation:* The LLM may hallucinate a compromise. This needs to be tracked during extraction.

## 2. Researcher & Logistics Agent (Mock Data) Edge Cases
- **Geographic Impossibilities:** User requests a road trip between non-connected continents (e.g., "Drive from Tokyo to San Francisco").
  - *Mitigation:* The LLM acting as the mock database must be prompted to return a standard "No Route Possible" error instead of hallucinating a magical bridge.
- **Hallucinating Non-existent Constraints:** The LLM might generate a hotel that costs $-50 or takes 0 minutes to travel.
  - *Mitigation:* Strict Pydantic validation on the output JSON. If `cost_per_night < 0`, the agent must retry or discard the option.

## 3. Reviewer Agent & Orchestration Edge Cases
- **Infinite Validation Loops:** The Reviewer rejects the Logistics agent's hotel choices because they exceed the budget. The Logistics agent tries again, but no hotels exist under the budget. They bounce back and forth infinitely.
  - *Mitigation:* The Orchestrator must implement a `MAX_RETRIES` counter (e.g., 3 loops). If exceeded, the system halts and returns a polite failure message to the user.
- **Formatting Failures:** The Reviewer produces a Markdown file, but the LLM breaks the markdown syntax or outputs raw JSON by mistake.
  - *Mitigation:* System prompts must heavily enforce markdown output rules, and a lightweight regex check can be used before presenting it to the user.
