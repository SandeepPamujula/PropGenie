# Milestone 7 — Integration Testing, Security Hardening & Launch Readiness

> **Goal:** End-to-end integration testing of the full agent pipeline, security hardening (input validation, CORS), performance validation against NFR targets, and final documentation for launch.

---

## US-33 — End-to-End Integration Tests

**User Story:**
As a **QA engineer**,
I want automated integration tests that exercise the full agent pipeline against a real (dev) environment,
So that I can validate the system works end-to-end before production releases.

**Tasks:**
- Create `backend/tests/integration/` directory
- Write `test_happy_path.py`: send a complete query, assert SSE events received in correct order (`agent_status` → `portal_card` × N → `search_meta` → `done`)
- Write `test_clarification_flow.py`: send ambiguous query, assert `clarification` event, respond, assert search completes
- Write `test_3_round_breach.py`: send maximally ambiguous query, respond vaguely 3 times, assert defaults applied and search completes
- Write `test_rate_limiting.py`: send 11 searches from the same test IP, assert 429 on the 11th
- Write `test_session_expiry.py`: create session, wait (or mock TTL), assert new session behavior
- All tests use the dev API endpoint and a dedicated test session prefix
- Add integration test step to the dev deploy pipeline (post smoke test)

**Acceptance Criteria:**
- Happy path test completes successfully with valid portal cards (NoBroker and/or 99acres)
- Clarification flow test receives exactly one question per round
- 3-round breach test receives results with default-applied notes
- Rate limit test correctly enforces the 10-search daily limit
- All integration tests pass against the dev environment
- Tests clean up their own session/rate-limit data

**Status:** Not Started

---

## US-34 — Input Validation & Sanitization

**User Story:**
As a **security engineer**,
I want all user inputs validated and sanitized before reaching the LLM,
So that the system is protected against prompt injection and malformed input attacks.

**Tasks:**
- Implement input validation in the Lambda handler (`backend/handler.py`) and FastAPI server (`backend/server.py`):
  - Message length: max 2000 characters; reject with 400 if exceeded
  - Session ID: must be valid UUID v4 format; reject with 400 if malformed
  - Content-Type: must be `application/json`; reject with 415 if incorrect
  - Message body: must contain `message` field as a non-empty string
- Implement basic prompt injection guards in the Orchestrator system prompt:
  - Instruct the LLM to ignore instructions embedded in user messages
  - Restrict output to property search domain only
- Sanitize user message before passing to LLM: strip control characters, normalize whitespace
- Write unit tests for all validation rules
- Write adversarial prompt injection tests (e.g., "ignore previous instructions and...")

**Acceptance Criteria:**
- Messages over 2000 characters return 400
- Invalid session ID format returns 400
- Missing/empty message field returns 400
- Prompt injection attempts are handled gracefully (system stays in property search domain)
- Control characters are stripped from user input
- All validation error responses include a user-friendly error message

**Status:** Not Started

---

## US-35 — Performance Validation

**User Story:**
As a **platform operator**,
I want performance benchmarks validating the system meets NFR latency targets,
So that I have confidence in the user experience before launch.

**Tasks:**
- Create `backend/tests/performance/` directory
- Write `test_latency_targets.py`:
  - Happy path end-to-end: assert < 8 seconds
  - First SSE event (`agent_status`): assert < 1 second
  - Clarification response: assert < 3 seconds
  - URL HEAD validation per portal: assert < 2 seconds
- Measure and log Lambda cold start times (assert < 3 seconds)
- Run performance tests 10 times and report P50, P95, P99 latencies
- Document results in `docs/performance-baseline.md`
- Identify optimization opportunities if targets are missed

**Acceptance Criteria:**
- Happy path P95 latency is under 8 seconds
- First SSE event P95 is under 1 second
- Cold start P95 is under 3 seconds
- Performance baseline document is created with benchmark results
- Any NFR misses are documented with mitigation plans

**Status:** Not Started

---

## US-36 — Documentation & Operational Runbook

**User Story:**
As a **new team member**,
I want comprehensive project documentation and an operational runbook,
So that I can set up the project locally, understand the architecture, and handle production incidents.

**Tasks:**
- Update `README.md` with:
  - Project overview and architecture summary
  - Prerequisites (Python 3.12, Node 20, Terraform, AWS CLI, MongoDB Atlas)
  - Local development setup instructions (backend FastAPI + frontend Next.js)
  - Environment variable reference table (referencing `.env.example`)
  - Links to HLD docs and backlog
- Create `docs/runbook.md`:
  - How to deploy to dev/prod manually
  - How to check Langfuse traces for debugging
  - How to investigate rate limit issues
  - How to add a new portal (config-only change)
  - How to update portal URL schemas when portals change
  - How to handle Lambda cold start spikes
  - How to roll back a bad deployment
- Create `docs/adr/001-monolithic-lambda.md`: why all agents run in a single Lambda
- Create `docs/adr/002-function-url-sse.md`: why Function URL (secured via OAC) is used instead of API GW for streaming
- Create `docs/adr/003-no-waf-v1.md`: why WAF is deferred to v2

**Acceptance Criteria:**
- A new developer can follow README to set up and run the project locally (both backend and frontend)
- Runbook covers the 7 most common operational scenarios
- ADRs explain key architectural decisions with context and tradeoffs
- All documentation is linked from the README

**Status:** Not Started

---

## US-37 — Portal Config Validation & Maintenance

**User Story:**
As a **platform operator**,
I want a scheduled validation job that checks portal URL schemas for drift,
So that I'm alerted when a portal changes its URL structure and can update configs promptly.

**Tasks:**
- Create `backend/scripts/validate_portals.py`:
  - Load both portal configs (NoBroker, 99acres)
  - Build a sample URL for each portal (using a standard Bangalore rental query)
  - Perform HTTP HEAD check against each sample URL
  - Report results: pass/fail per portal with HTTP status code
- Create a GitHub Actions scheduled workflow (`.github/workflows/portal-check.yml`):
  - Runs weekly (Sunday midnight IST)
  - Executes `validate_portals.py`
  - Opens a GitHub issue if any portal fails validation
- Document the portal update process in the runbook (US-7.4)

**Acceptance Criteria:**
- Validation script checks both portals and reports results
- Scheduled workflow runs weekly without manual intervention
- A GitHub issue is auto-created when a portal fails validation
- Issue includes the portal name, expected vs actual HTTP status, and the sample URL
- Runbook documents how to update a portal config after schema drift

**Status:** Not Started
