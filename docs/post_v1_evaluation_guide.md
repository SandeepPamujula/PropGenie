# Post-V1 Evaluation Guide

Based on a thorough review of the High-Level Design (HLD) and the backlog documentation, here is a breakdown of how key evaluation metrics are considered in the current V1 design, along with strategies for measuring them post-launch:

### 1. Evaluating Hallucinations
**Considered in V1:** Yes. The HLD explicitly identifies LLM hallucination (especially fabricating locality names or invalid URL parameters) as a major risk (Risk R2 in `10-risks-and-roadmap.md`). 
**How it is handled/measured:**
*   **Current Proxy Metric:** We are using the **URL Validator Agent** as a deterministic check. If the LLM hallucinates an invalid parameter, the generated URL will fail the structural or liveness (HTTP HEAD) check.
*   **Measurement:** When a URL is dropped by the validator, a **"hallucination flag"** is set in the Langfuse trace (`milestone_5_rate_limiting_observability.md`). 
*   **Post-V1 Action:** You can use Langfuse dashboards to measure the hallucination rate (percentage of generated URLs that fail validation). If the rate is high, the roadmap suggests transitioning to a deterministic Geocoding API (like Google Maps/Nominatim) in V2 to eliminate location-based hallucinations.

### 2. Model Benchmarking
**Considered in V1:** Yes, as part of the launch hardening phase. `milestone_7_testing_hardening_launch.md` explicitly includes tasks to run performance benchmarks to ensure the system meets NFRs.
**How it is handled/measured:**
*   **Measurement:** We will be running automated benchmark tests (e.g., `test_latency_targets.py`) against a standard dataset of representative inputs to generate a "Performance Baseline Document."
*   **Post-V1 Action:** Since every LLM call (Orchestrator, Clarification, Query Builder) is instrumented with Langfuse, you will have continuous benchmarking out-of-the-box. You can track metrics like:
    *   **Tokens per second** (Generation speed)
    *   **Time to First Token (TTFT)**
    *   **Cost per query** (Bedrock cost estimation tracked per span)

### 3. Latency Optimization
**Considered in V1:** Highly prioritized. The NFR target for end-to-end latency is **< 8 seconds** (`07-nfr-summary.md`). 
**How it is handled/measured:**
*   **Architectural Optimization:** To minimize latency, the HLD explicitly chose a **Monolithic Lambda topology** (running the entire LangGraph in one function). This intentionally avoids the cold starts and network overhead of inter-Lambda communication (`01-executive-summary.md`). We are also using direct CloudFront-to-Lambda streaming.
*   **Measurement:** Latency (`latency_ms`) is tracked at both the graph level and the individual agent span level via Langfuse. 
*   **Post-V1 Action:** If P95 latency exceeds 8 seconds, you can look at the Langfuse waterfall traces to pinpoint exactly which agent or HTTP call (e.g., LLM generation vs. URL HEAD request) is the bottleneck and optimize accordingly.

### 4. Retrieval Strategies
**Considered in V1:** Not directly applicable to the current architectural flow. 
**How it is handled/measured:**
*   PropGenie V1 operates differently from a traditional RAG (Retrieval-Augmented Generation) system. Instead of retrieving documents from a Vector DB to feed the LLM, the system acts as a **Query Builder**—it extracts entities and maps them directly to public real estate portal URL structures.
*   **Post-V1 Action:** Because we aren't using vector retrieval, standard retrieval metrics (like NDCG or Precision@K) don't apply yet. Instead, the equivalent metric to measure is **Entity Resolution Accuracy**—how often the orchestrator correctly maps user input to the correct internal schema. If PropGenie later evolves to scrape and ingest actual listing data into a vector store, we will need to implement standard RAG chunking, embedding, and retrieval measurement pipelines.

### 5. Prompt Architecture
**Considered in V1:** Yes. Prompts are treated as core system components and are heavily documented in the backlog (`milestone_2_core_agent_pipeline.md`).
**How it is handled/measured:**
*   **Design:** We have distinct, scoped system prompts for the Orchestrator and Clarification agents. There is also an explicit requirement for **Prompt Injection Guards** hardened directly into the Orchestrator prompt to ensure the agent stays within the property search domain (`milestone_7_testing_hardening_launch.md`).
*   **Measurement:** The exact inputs and outputs of every prompt are captured in Langfuse traces. 
*   **Post-V1 Action:** Langfuse provides a feature called **Datasets**. You can curate a golden dataset of user queries and run your prompt iterations against them. This allows you to quantitatively measure if a new prompt version improves accuracy or degrades performance before deploying it to production. You can also implement user feedback mechanisms (thumbs up/down) to attach scores directly to specific prompt traces.
