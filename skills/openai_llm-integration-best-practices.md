# OpenAI: LLM Integration & Prompt Engineering

## 🎯 Goal
Optimize code that interacts with Large Language Models (OpenAI, Gemini, Local Models) for stability, cost-efficiency, and predictable outputs.

## 📋 Core Directives
- **System Prompts Isolation:** Keep system prompts, dictionaries, and translation instructions out of the main code logic. Store them in YAML/JSON configuration files.
- **Strict Output Parsing:** When expecting JSON from an LLM, always enforce structured outputs or JSON Mode. Use tools like `Pydantic` to immediately validate the LLM's response upon receipt.
- **Token Efficiency:** Avoid sending redundant context. Pre-process and chunk input data strictly before sending it to the LLM to save tokens and prevent context overflow.
- **Retry Mechanisms:** Wrap all LLM network calls with exponential backoff and retry logic (e.g., using `tenacity` or `asyncio.sleep`) to handle rate limits and transient server errors gracefully.
- **Streaming Handlers:** If implementing streaming outputs, ensure the UI thread is never blocked. Yield chunks asynchronously to the frontend.
