# Milestone 5 — Rate Limiting, Search Logging & Observability

> **Goal:** Implement rate limiting within the agent handler, search analytics logging, Langfuse LLM tracing across all agent nodes, and CloudWatch custom metrics. This milestone completes the operational readiness layer.

---

## US-5.1 — Rate Limit Logic in Agent Handler

**User Story:**
As a **platform operator**,
I want IP-based rate limiting enforced directly in the Agent Lambda/Server handler,
So that individual IPs are limited to 10 searches per day and the system is protected from abuse while still supporting SSE streaming.

**Tasks:**
- Implement `backend/utils/rate_limiter.py`:
  - Extract client IP from the request (from CloudFront `CloudFront-Viewer-Address` header in AWS, or request context locally)
  - Query MongoDB `rate_limits` collection: `find({ip, date: today_IST_string})`
  - If `count >= 10`, raise a RateLimitException to return a 429 response body
  - If `count < 10` or no record exists, allow the request to proceed
- Implement IST date calculation (UTC+5:30) for the `date` field
- Handle MongoDB connection errors gracefully (return allow on DB failure — fail open, log error)
- Integrate this check at the very beginning of the `backend/handler.py` and `backend/server.py` execution
- Write unit tests with mocked MongoDB

**Acceptance Criteria:**
- IP with 0–9 searches today is allowed through
- IP with 10+ searches today receives a 429 response with the friendly message from the API contract
- Rate limit check uses IST calendar day (not UTC)
- MongoDB connection failure results in allow (fail-open) with an error log

**Status:** Completed

---

## US-5.2 — Rate Limit Counter Increment

**User Story:**
As a **platform operator**,
I want the search counter incremented only on successful search completions (not clarification exchanges),
So that rate limiting accurately reflects actual search usage.

**Tasks:**
- Add rate limit increment logic to the `save_state` graph node (runs after `response_formatter`):
  - `updateOne({ip, date: today_IST_string}, {$inc: {count: 1}, $set: {last_incremented: now, expires_at: today_IST_midnight + 2_days}}, {upsert: true})`
  - Only increment when the graph reached the `response_formatter` node (not on clarification exit)
- Create MongoDB compound unique index: `{ip, date}` for atomic upsert
- Create TTL index on `expires_at` field (ISODate) for automatic cleanup
- Write unit tests verifying increment only on search completion

**Acceptance Criteria:**
- Counter increments by 1 after a successful search flow
- Counter does not increment after a clarification-only interaction
- Upsert creates a new record if none exists for today's date
- TTL automatically removes records when `expires_at` is reached (~2 days)
- Concurrent increments from the same IP are handled atomically (no race condition)

**Status:** Not Started

---

## US-5.3 — Search Analytics Logging

**User Story:**
As a **product analyst**,
I want every completed search logged with full context to the `search_logs` collection,
So that I can analyze search patterns, popular cities, and portal performance over time.

**Tasks:**
- Implement `backend/db/search_logger.py`:
  - `log_search(session_id, ip, state)` function
  - Construct the log document per the data schema:
    - `ip_hash`: SHA-256 of the raw IP (never store raw IP in logs)
    - `intent`, `city`, `location_anchor`, `property_type`, `bhk`, `budget_min`, `budget_max`, `radius_km`
    - `portals_searched`, `portals_returned`, `portals_dropped`, `clarification_rounds`, `defaults_applied`
    - `latency_ms`: total graph execution time
    - `llm_calls`: number of LLM invocations in this search
    - `total_input_tokens`, `total_output_tokens`: aggregate token usage
    - `timestamp`: current UTC ISO timestamp
  - Insert into `search_logs` collection
- Create MongoDB indexes programmatically:
  - `timestamp` index for time-range queries
  - `city` index for aggregation
  - `intent` index for distribution analysis
- Integrate the logger into the `save_state` node (log only on search completion, not clarification)
- Write unit tests for IP hashing and document construction

**Acceptance Criteria:**
- Every completed search produces exactly one `search_logs` document
- Raw IP is never stored — only `ip_hash` (SHA-256)
- All entity fields from the resolved state are present in the log
- `portals_dropped` correctly lists portals excluded by URL validation
- `latency_ms` accurately reflects end-to-end graph execution time
- Token usage (input/output) is captured per search
- Clarification-only interactions do not produce a search log

**Status:** Not Started

---

## US-5.4 — Langfuse LLM Tracing

**User Story:**
As a **platform operator**,
I want every agent invocation traced in Langfuse with per-span metrics,
So that I can monitor LLM performance, detect hallucinations, and track costs.

**Tasks:**
- Create `backend/observability/langfuse_tracer.py`:
  - Initialize Langfuse client with credentials from environment variables
  - `create_trace(session_id)` — creates a trace tied to the session
  - `create_span(trace, agent_name, input_data)` — creates a span for each agent node
  - `end_span(span, output_data, metrics)` — records latency, token counts, cost estimate
- Instrument each agent node with Langfuse spans:
  - **Orchestrator**: input = user message, output = classified intent + entities, metrics = tokens, latency
  - **Clarification**: input = missing fields, output = clarification question, metrics = tokens, latency
  - **Query Builder**: input = resolved entities, output = generated URLs, metrics = tokens, latency
  - **URL Validator**: input = generated URLs, output = validated URLs, metrics = latency, hallucination flag (URLs dropped)
  - **Response Formatter**: input = validated URLs, output = formatted cards, metrics = latency
- Set hallucination flag when URL Validator drops URLs (proxy metric)
- Record clarification round count per trace
- Write unit tests with mocked Langfuse client

**Acceptance Criteria:**
- Every graph invocation creates one Langfuse trace with the session ID
- Each agent node produces a span with input/output recorded
- Token counts and latency are captured for LLM-calling agents (Orchestrator, Clarification, Query Builder)
- Hallucination flag is set when any URL fails validation
- Traces are visible in the Langfuse dashboard with correct session grouping
- Langfuse client failures are caught and logged — never crash the agent pipeline

**Status:** Not Started

---

## US-5.5 — CloudWatch Custom Metrics

**User Story:**
As a **platform operator**,
I want custom CloudWatch metrics for rate limit breaches and agent-level performance,
So that I can set up dashboards and alarms for operational visibility beyond default Lambda metrics.

**Tasks:**
- Implement structured logging in the Agent Lambda using Python `logging` with JSON format
- Add log markers for CloudWatch metric filters:
  - `RATE_LIMIT_EXCEEDED` — logged by the rate limiter on deny
  - `SEARCH_COMPLETED` — logged by the agent on successful search
  - `CLARIFICATION_ROUND` — logged per clarification exchange
  - `URL_VALIDATION_FAILED` — logged per dropped URL
  - `BEDROCK_CALL` — logged per LLM invocation with latency
- Configure structured log output compatible with CloudWatch metric filter patterns
- Write a shared logging utility `backend/utils/logger.py` with consistent format across all modules

**Acceptance Criteria:**
- All log entries are JSON-formatted with `level`, `message`, `timestamp`, `request_id` fields
- Rate limit breaches are logged with the `RATE_LIMIT_EXCEEDED` marker
- CloudWatch metric filters (defined in Terraform) can parse the log markers
- Log levels are appropriate: INFO for normal operations, WARNING for rate limits, ERROR for failures
- No sensitive data (raw IP, MongoDB URI) appears in logs

**Status:** Not Started
