# magicpin AI Challenge Submission

## 1. Approach
Our approach leverages a structured prompt and a frontier LLM (defaulting to Llama 3.1 70B via OpenRouter) to directly compose personalized messages based on the four provided contexts. 

- **Composition Logic**: The four contexts (Category, Merchant, Trigger, and optionally Customer) are stringified into a JSON block and passed to the LLM. The system prompt heavily emphasizes the evaluation criteria (Specificity, Category fit, Merchant fit, Trigger relevance, and Engagement compulsion).
- **FastAPI Harness**: We implemented the required API endpoints (`/v1/context`, `/v1/tick`, `/v1/reply`, `/v1/healthz`, `/v1/metadata`). The `/v1/context` endpoint builds an in-memory state, and `/v1/tick` parses the requested triggers, retrieves their dependencies, and invokes the `compose()` function.
- **Multi-turn handling**: In the `/v1/reply` endpoint, we included a lightweight heuristic-based router. It identifies typical auto-reply markers (e.g., "automated assistant") or rejections ("not interested", "stop") and exits the conversation gracefully, avoiding repetitive turns. If a merchant demonstrates positive intent, it smoothly acknowledges and transitions to a positive outcome state.

## 2. Tradeoffs Made
- **In-memory state vs Database**: Given the 60-minute duration and isolated test runs of the judge harness, the context and conversation history are persisted purely in-memory. This allows fast development and execution without the overhead of a database (e.g. Redis/SQLite). If the system was going to production or handling massive concurrency across sessions, this would be swapped out.
- **LLM Call per Action**: In `/v1/tick`, we currently process and compose triggers synchronously using the LLM. To meet the 30-second timeout across many available triggers, we iterate through them in order. For larger parallel executions, a more robust task queuing system would be needed to ensure timeouts are not breached.
- **Zero-shot vs RAG/Few-shot**: We are using a robust zero-shot instruction with the full context payloads injected into the prompt. A tradeoff was made not to build a RAG layer over the `digest` or `patient_content_library`, as the context window is sufficiently large to hold the current test categories.

## 3. Additional Context That Would Have Helped
- **Previous Conversation Examples**: Including a library of 'successful' vs 'unsuccessful' past chats (beyond the brief's patterns) in the base context would allow the LLM to few-shot align its tone and strategy even closer to the current highest-performing baseline.
- **Merchant Persona Indicators**: An explicit label of how "tech-savvy" or "busy" a merchant historically acts would help tweak the length and density of the composed messages.
