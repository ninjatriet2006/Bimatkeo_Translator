# Trailofbits: Ask Questions If Underspecified

## 🎯 Goal
Prevent the AI agent from hallucinating requirements, making blind assumptions, or writing incorrect logic when the user's prompt is missing critical technical constraints.

## 📋 Core Directives
- **Halt on Ambiguity:** If a request lacks edge-case definitions, fallback strategies, or structural constraints (e.g., JSON schema), STOP and explicitly ask the user to clarify.
- **Do Not Guess API Specs:** When interacting with undocumented or partially documented APIs, ask for the payload schema rather than assuming it.
- **Failure Modes:** Always inquire about what should happen if a component fails: "Should the system crash, retry, or silently log the error?"
- **Propose Options:** When halting to ask a question, provide 2 or 3 technically viable options to guide the user (e.g., "Option A: Retry 3 times. Option B: Throw immediate error").
- **Strict Compliance:** Do not proceed with code generation until the ambiguity is resolved by the user.
