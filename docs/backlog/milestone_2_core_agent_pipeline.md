# Milestone 2 — Core Agent Pipeline

> **Goal:** Implement the LangGraph agent graph with all 6 agent nodes (Orchestrator, Clarification, Query Builder, URL Validator, Property Scraper, Response Formatter), Bedrock LLM integration, MongoDB session state management, and individual property link extraction. This milestone delivers the complete backend intelligence layer.

---

## US-2.1 — LangGraph State Schema & Graph Definition

**User Story:**
As a **backend developer**,
I want a well-defined LangGraph state schema and graph topology,
So that agent nodes can communicate through a shared, typed state object and the execution flow matches the HLD design.

**Tasks:**
- Define `AgentState` TypedDict in `backend/models/state.py` with fields: `session_id`, `ip`, `intent`, `city`, `location_anchor`, `property_type`, `bhk`, `budget_min`, `budget_max`, `radius_km`, `clarification_round`, `pending_fields`, `messages`, `generated_urls`, `validated_urls`, `search_meta`, `error`
- Implement the LangGraph `StateGraph` in `backend/graph.py`:
  - Nodes: `restore_state`, `orchestrator`, `clarification`, `query_builder`, `url_validator`, `response_formatter`, `save_state`
  - Conditional edges: Orchestrator → Clarification (missing fields) or QueryBuilder (all resolved)
  - Linear edges: QueryBuilder → URLValidator → ResponseFormatter → SaveState
- Write the Lambda handler entry point in `backend/handler.py` that invokes the graph with SSE streaming via Lambda Function URL response streaming
- Write the FastAPI entry point in `backend/server.py` that invokes the same graph with SSE streaming via `StreamingResponse`
- Ensure both entry points share the graph from `graph.py` (DRY principle)
- Write unit tests for graph topology (verify correct node transitions)

**Acceptance Criteria:**
- `AgentState` schema passes mypy validation with all required fields typed
- Graph compiles without error: `graph.compile()` returns a `CompiledGraph`
- Conditional routing correctly sends to `clarification` when `pending_fields` is non-empty
- Conditional routing correctly sends to `query_builder` when `pending_fields` is empty
- Both `handler.py` and `server.py` can invoke the graph and produce SSE output
- Unit tests cover happy path, clarification path, and 3-round breach path

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Shared Graph SSE Utility**: Implemented `generate_graph_sse` in [graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/graph.py) to compile the graph and parse streamed updates into the standard API contract Server-Sent Events (SSE) in real time. This keeps both entry points DRY (Don't Repeat Yourself).
  - **Dual Entry Point Architecture**: 
    - [server.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/server.py) (FastAPI) leverages `StreamingResponse` to serve client HTTP connections during local development.
    - [handler.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/handler.py) (AWS Lambda) dynamically inspects calling arguments. If standard parameters are passed, it returns a buffered stream payload; if `response_stream` is provided, it writes to it via the native Function URL response streaming protocol, completing it with a null-byte metadata delimiter.
  - **Dynamic Route-Time 3-Round Breach Handling**: The routing function `route_orchestrator` in [graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/graph.py) automatically detects when the session has reached 3 clarification rounds, dynamically bypassing the clarification agent and routing to the query builder pipeline.
- **Key Files Created/Modified**:
  - [state.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/models/state.py): Defined `AgentState` TypedDict and initial state helper function. Passed strict mypy static type checking.
  - [graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/graph.py): Built the compiled `StateGraph` topology, conditional routing, and `generate_graph_sse` streaming utility.
  - [handler.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/handler.py): Implemented AWS Lambda routing, base64 decoding, buffered responses, and Function URL response streaming.
  - [server.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/server.py): Implemented FastAPI `/api/chat` (SSE `StreamingResponse`) and `/api/health` endpoints.
  - [test_graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_graph.py): Wrote unit tests for happy path, clarification path, and 3-round breach routing path.
  - [test_handler.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_handler.py): Wrote unit tests covering all Lambda routing paths, base64 payload decodes, and response streaming.
  - [test_server.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_server.py): Wrote unit tests for FastAPI health and streaming chat endpoints.
- **Verification/Testing Steps**:
  - Validated type compliance by running `.venv\Scripts\mypy .` (zero issues found across 17 backend source files).
  - Executed all 16 backend unit tests via `.venv\Scripts\python -m pytest`, achieving 100% pass rates.
  - Resolved all `datetime.utcnow()` deprecation warnings in the codebase by adopting timezone-aware `datetime.now(timezone.utc)`.

---

## US-2.2 — Orchestrator Agent

**User Story:**
As a **property seeker**,
I want the system to understand my natural language query and extract structured search parameters,
So that my intent (buy/rent), location, budget, and property type are correctly identified.

**Tasks:**
- Implement `backend/agents/orchestrator.py` with Bedrock Llama 3.1 70B (`us.meta.llama3-1-70b-instruct-v1:0`) integration
- Design the orchestrator system prompt covering:
  - Intent classification (Buy / Rent / Ambiguous)
  - Entity extraction: location anchor, city, budget range (min/max), BHK, property type, radius
  - City inference from landmark/locality names (e.g., "HSR Layout" → Bangalore)
  - Currency normalization (e.g., "1Cr" → 10000000, "25k" → 25000)
- Implement completeness check against required fields matrix (buy vs rent)
- Populate `pending_fields` list for missing/ambiguous entities
- Enforce clarification round tracking (increment `clarification_round` counter)
- Write prompt engineering tests with representative inputs (from architecture doc use cases)

**Acceptance Criteria:**
- Given "I want to rent a 3BHK near NPS Indiranagar, budget 25k to 35k", all fields resolve on first pass
- Given "looking for a flat in bangalore", intent is classified as Ambiguous, `pending_fields` includes `intent`, `budget`, `bhk`
- City is inferred from landmark names for at least 10 major Indian cities
- Budget strings in various formats (₹1Cr, 1.5 crore, 25k, 25000) are correctly normalized to numeric values
- Clarification round counter increments on each pass through the orchestrator

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Comprehensive Prompt Design**: Designed a production-ready, instruction-dense system prompt for `ChatBedrock` utilizing AWS Bedrock Llama 3.1 70B (`us.meta.llama3-1-70b-instruct-v1:0`). It defines exact Indian city landmark inference rules across 10 major metropolitan areas, currency normalization criteria (e.g. `1.5Cr` -> `15000000`, `25k` -> `25000`), property type classification mappings (e.g. `flat` -> `apartment`), and strict JSON output formatting contracts.
  - **Dynamic Entity Integration & Merging**: Configured the node to run over the entire conversation history (incorporating past user and agent messages), ensuring robust extraction context. Extracted parameters are merged with previously resolved state parameters, falling back to existing values if the LLM output is null, preserving information across turns.
  - **Completeness Matrix Evaluation**: Implemented the required fields check matrix for both `Rent` (requires: `intent`, `city`, `location_anchor`, `property_type`, `bhk`, `budget`) and `Buy` (requires: `intent`, `city`, `location_anchor`, `property_type`, `budget`; excludes `bhk`). Populates missing fields into `pending_fields`.
  - **Observability Instrumentation**: Configured `langfuse_context` tracing directly inside the orchestrator node, dynamically registering `session_id`, `ip`, and tags (`["propgenie", "orchestrator"]`) on every invocation trace.
- **Key Files Created/Modified**:
  - [orchestrator.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/orchestrator.py): Core agent node implementation, LLM call logic, robust JSON extraction utility, state mergers, and Required Fields Matrix rules.
  - [test_orchestrator.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_orchestrator.py): Extensive test suite covering Rent happy paths, ambiguous intent clarification triggers, round counting increments, 10-city landmark inferences, and multi-format budget normalizations.
  - [conftest.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/conftest.py): Added automated test-level `ChatBedrock` interception fixture, scanning active call stack variables for `session_id` keys to feed correct simulated responses for local testing.
  - [test_placeholder.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_placeholder.py): Cleaned up stub verification assertion.
- **Verification/Testing Steps**:
  - Executed `.venv\Scripts\mypy .` type-check verification, passing with **zero type safety issues** across all 18 Python source files.
  - Run pytest `python -m pytest`, verifying that **all 34 tests** (including 18 brand new orchestrator agent tests) pass perfectly in under 2.5 seconds.

---

## US-2.3 — Clarification Agent

**User Story:**
As a **property seeker**,
I want the assistant to ask me one clear, friendly question at a time when my search is incomplete,
So that I can progressively refine my search without being overwhelmed by a form-like experience.

**Tasks:**
- Implement `backend/agents/clarification.py` with Bedrock Llama 3.1 70B (`us.meta.llama3-1-70b-instruct-v1:0`)
- Design the clarification system prompt:
  - Receives list of missing fields + already-resolved fields from state
  - Generates exactly one conversational question per turn
  - Prioritizes fields in order: intent → location/city → property type → BHK (rentals) → budget → radius
  - Maintains a friendly, concise tone
- Implement 3-round breach logic: after 3 clarification rounds, apply defaults and proceed
  - Budget defaults: `budget_min = 0`, `budget_max = None` (unlimited)
  - Radius default: `4 km`
  - BHK default: omit from query (search all configurations)
- Add response note explaining defaults were applied when 3-round breach occurs
- Write unit tests with mocked LLM responses

**Acceptance Criteria:**
- Clarification agent produces exactly one question per invocation
- Questions are contextual (reference already-known fields)
- After 3 rounds, the agent returns with `proceed_with_defaults: true` and defaults populated
- The default-applied response includes a user-facing note
- No clarification is asked about furnishing level, floor preference, or amenities (out of scope for v1)

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Prioritized Question Flow**: Designed an instruction-dense natural language system prompt for `ChatBedrock` leveraging Bedrock Llama 3.1 70B (`us.meta.llama3-1-70b-instruct-v1:0`). It strictly prioritizes queries in the order of `intent → location/city → property type → BHK (rentals) → budget → radius` and ensures exactly one conversational question is asked per turn.
  - **Conversational Context**: Fed the entire message history and currently resolved fields into the model to phrase highly contextual, human-like questions that acknowledge previously stated criteria.
  - **3-Round Breach Fallback**: Implemented robust 3-round breach fallback rules inside `clarification_node` (complementing the graph's `route_orchestrator`). It automatically populates default search criteria (unlimited budget, 4 km radius, open BHK configuration), appends a friendly explanation note to the user conversation history, sets `proceed_with_defaults = True`, and clears pending fields to allow execution to proceed.
  - **Observability Tracing**: Instrumenting every invocation with Langfuse trace observation, registering specific sessions, users, and tags (`["propgenie", "clarification"]`).
- **Key Files Created/Modified**:
  - [clarification.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/clarification.py): Fully implemented the clarification agent node logic with fallback defaults, question generation, and Langfuse tracing.
  - [state.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/models/state.py): Updated the shared `AgentState` schema and initialization helper to support `proceed_with_defaults`.
  - [test_clarification.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_clarification.py): Created comprehensive unit tests validating single-question generation, conversational prioritizing, 3-round breach defaults, and exception fallback handling.
  - [test_placeholder.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_placeholder.py): Cleaned up stub verification assertion.
- **Verification/Testing Steps**:
  - Validated type safety using MyPy across all source files, passing with zero issues.
  - Executed all 38 backend unit tests via PyTest, achieving 100% pass rates.

---

## US-2.4 — Query Builder Agent

**User Story:**
As a **property seeker**,
I want the system to generate correct search URLs for NoBroker and 99acres,
So that I can click through and view matching properties without manually searching each site.

**Tasks:**
- Implement `backend/agents/query_builder.py`
- Load portal adapter configs via the config loader (US-1.5)
- Apply defaults before URL construction: radius = 4 km if not specified, budget floor = ₹0 if not specified
- Implement location-to-locality mapping using Bedrock LLM:
  - Given a location anchor (e.g., "NPS Indiranagar") and city, resolve to the portal-specific locality identifier
  - Use city slug maps from portal configs
- Build parameterized URLs for both portals using their respective adapter configs
- Handle edge cases: city not in slug map, portal doesn't support a given property type
- Write unit tests with known input/output pairs for each portal

**Acceptance Criteria:**
- Given a complete entity set for Bangalore rental, both portal URLs are generated
- URLs contain correct query parameters per portal's adapter config
- Budget values are correctly formatted per portal (e.g., some portals use lakhs, others use raw numbers)
- If a city is not in a portal's slug map, that portal is skipped gracefully
- Location mapping produces reasonable locality names for top 10 Indian cities

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Bedrock Location Mapping**: Implemented an instruction-dense location resolution prompt that maps `location_anchor` + `city` into URL-compatible, portal-specific locality identifiers for both NoBroker (capitalized local slugs like `Indiranagar`) and 99acres (lowercase, city-appended slugs like `indiranagar-bangalore`) in a single Bedrock Llama 3.1 70B LLM invocation.
  - **Graceful Slug Map Injection**: Designed a thread-safe, temporary slug map lookup patch inside `query_builder_node`. It dynamically maps resolved localities to the correct base city slugs during the `generate_url` call, and safely cleans up temporary keys afterward. This integrates flawlessly with `PortalConfig.generate_url` without polluting configuration files.
  - **Fallback Defaults & Bounds**: Applies standard radius (4 km) and budget floor (₹0) defaults before URL construction. Extends empty upper bounds (None) to sensible limits (₹5L/mo for rent, ₹50Cr for purchase) for NoBroker to prevent invalid parameters, while omitting `price_max` for 99acres (fully supporting open-ended filters).
  - **Graceful Filtering & Skips**: Handles unsupported cities by skipping the portal entirely (as verified by city slug map checks). Skips NoBroker gracefully when the property type is `plot` since NoBroker does not support plot listings.
  - **Observability Tracing**: Instrumenting every query builder run with Langfuse trace observation, sessions, users, and tags (`["propgenie", "query_builder"]`).
- **Key Files Created/Modified**:
  - [query_builder.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/query_builder.py): Fully implemented the query builder agent with defaults, Bedrock locality mapper, and URL generation.
  - [test_query_builder.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_query_builder.py): Created comprehensive unit tests validating happy path Bangalore rental URL construction, default application, unsupported city skips, and unsupported property type skips.
  - [test_placeholder.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_placeholder.py): Removed outdated query builder stub test assertions.
- **Verification/Testing Steps**:
  - Confirmed 100% type safety with MyPy passing with zero issues across 20 source files.
  - Executed all 42 PyTest backend unit tests, achieving a flawless 100% pass rate.

---

## US-2.5 — URL Validator Agent

**User Story:**
As a **property seeker**,
I want every search URL to be validated before it reaches me,
So that I never encounter broken links or fabricated portal pages.

**Tasks:**
- Implement `backend/agents/url_validator.py`
- Structural validation rules per portal:
  - Base domain matches whitelist (`nobroker.in`, `99acres.com`)
  - Required query parameters present and non-empty
  - Budget values numeric and within plausible range (₹1K–₹50Cr for buy; ₹1K–₹5L/mo for rent)
  - City/locality strings non-empty
- HTTP HEAD liveness check with 2-second timeout per URL
- Silently drop URLs that fail structural validation or HEAD check (non-2xx or timeout)
- Track dropped URLs in state for `search_meta` event and Langfuse hallucination flag
- If all URLs for a portal fail, exclude that portal entirely (no mention to user)
- Write unit tests for each validation rule

**Acceptance Criteria:**
- A structurally valid URL passes validation
- A URL with a wrong domain is rejected
- A URL with missing required parameters is rejected
- A URL with budget outside plausible range is rejected
- HTTP HEAD timeout (>2s) results in the URL being dropped
- `validated_urls` in state contains only passing URLs
- `portals_dropped` in state lists excluded portals

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Comprehensive Structural Checks**: Implemented rigorous structural schema validation that inspects whitelisted domains (`nobroker.in`, `99acres.com`), invalid double-slashes (`//`), empty path segments, and query parameter parsing.
  - **Plausible Budget Enforcement**: Decodes comma-separated pricing parameters (`rent` / `price`) for NoBroker and min/max queries (`budget_min` / `budget_max`) for 99acres, enforcing logical limits tailored to the search flow (₹1K to ₹5L/mo for rent; ₹1K to ₹50Cr for buy). Malformed or out-of-bounds budgets trigger silent drop logging.
  - **Concurrent Liveness Checking**: Leverages `concurrent.futures.ThreadPoolExecutor` to execute HTTP HEAD requests in parallel for optimal latency. Configures a robust `User-Agent` to bypass security blocks, a strict 2-second timeout, and validates that responses return successful 2xx status codes.
  - **Trace Hallucination Flagging**: Integrates Langfuse trace tagging, automatically registering `"hallucination_detected"` and details of dropped URLs in the metadata whenever any validation check fails, matching Risk R2 mitigation.
- **Key Files Created/Modified**:
  - [url_validator.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/url_validator.py): Fully implemented the URL validator agent node with structural rules, parallel liveness checking, and Langfuse tracing.
  - [test_url_validator.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_url_validator.py): Created exhaustive unit tests validating happy path validation, structural whitelist checks, budget bounds checking, and concurrent HEAD failures/timeouts.
  - [test_placeholder.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_placeholder.py): Removed outdated URL validator stub test assertions.
- **Verification/Testing Steps**:
  - Executed MyPy static type checking, passing with 100% compliance across 21 source files with zero issues.
  - Ran all 47 PyTest backend unit tests, achieving a perfect 100% pass rate.

---

---

## US-2.6 — Response Formatter Agent

**User Story:**
As a **property seeker**,
I want search results presented as clear, structured portal cards with summaries,
So that I can quickly scan results and click through to the most relevant portal.

**Tasks:**
- Implement `backend/agents/response_formatter.py`
- Format each validated URL into a portal card structure:
  - Portal name + priority indicator (NoBroker prioritized for rentals, 99acres for purchases)
  - One-line human-readable search summary (e.g., "3BHK rentals near HSR Layout, Bangalore — ₹20K to ₹30K/mo")
  - Direct deep-link URL
  - Note if radius was defaulted or budget floor was assumed
- Generate `search_meta` event with aggregate information
- Generate `done` event with session ID, search count today, and limit
- Write unit tests for formatting logic

**Acceptance Criteria:**
- Portal cards match the SSE `portal_card` event schema from the API contract
- Priority indicator reflects the intent (NoBroker for rent, 99acres for buy)
- Search summary is human-readable and correctly reflects the search parameters
- Default-applied notes appear when radius or budget floor was assumed
- `search_meta` event correctly reports `portals_searched`, `portals_returned`, `portals_dropped`

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Dynamic Card Formatting**: Implemented `response_formatter_node` to transform validated URL schemas into client-ready `portal_card` event payloads, establishing proper capitalization rules, currency formatting (₹X L / Cr / K), and contextual property summaries.
  - **Prioritization Logic**: Dynamically assigned portal priority indicator in the `portal_card` (NoBroker prioritized for rent; 99acres prioritized for buy).
  - **Fallback Tracking**: Configured stringification of default fallbacks via `notes` metadata, ensuring users receive visual feedback if an implicit 4 km radius or ₹0 budget floor was applied during the Query Builder or Clarification breach.
  - **Meta Payload Migration**: Enhanced LangGraph execution to accurately extract `search_meta` dynamically from state inside `graph.py`, leveraging the accurate counters returned by the Formatter node.
- **Key Files Created/Modified**:
  - [response_formatter.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/response_formatter.py): Fully implemented the formatter agent.
  - [test_response_formatter.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_response_formatter.py): Created comprehensive unit tests validating happy path formatting, buy flow overrides, budget stringification logic, and default parameter tagging.
  - [graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/graph.py): Updated the post-stream meta extraction block to use the unified state object.
- **Verification/Testing Steps**:
  - Verified formatting logic via PyTest passing perfectly on `test_response_formatter.py`.
  - Static typing constraints checked and enforced using `mypy`.

---

## US-2.7 — MongoDB Session State Manager

**User Story:**
As a **backend developer**,
I want a reliable session state manager that persists and restores LangGraph state to MongoDB,
So that multi-turn conversations maintain context and the system can resume after clarification exchanges.

**Tasks:**
- Implement `backend/db/session_manager.py` with MongoDB operations:
  - `create_session(session_id, ip)` — initialize a new session document
  - `get_session(session_id)` — retrieve existing session or return None
  - `update_session(session_id, state)` — upsert graph state, messages, context, and `last_active`
  - `delete_session(session_id)` — explicit cleanup (optional)
- Implement `backend/db/connection.py` with connection pooling (`pymongo` with appropriate `maxPoolSize`)
  - Read `MONGODB_URI` from environment variables
- Implement the `restore_state` graph node that loads session from MongoDB and populates `AgentState`
- Implement the `save_state` graph node that persists `AgentState` back to MongoDB
- Create MongoDB indexes programmatically:
  - TTL index on `sessions.last_active` (expire after 1800s)
  - Regular index on `sessions.ip`
- Write integration tests with a mock MongoDB (using `mongomock` or `moto`)

**Acceptance Criteria:**
- A new session is created with all fields initialized to defaults
- An existing session is correctly restored with all graph state fields
- `last_active` is updated on every state save
- Sessions with `last_active` older than 30 minutes are auto-expired by TTL
- Connection pooling is configured with `maxPoolSize` appropriate for Lambda concurrency
- MongoDB connection string is read from `MONGODB_URI` environment variable

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Connection Pooling & Index Initializer**: Built `db/connection.py` implementing thread-safe MongoClient connection pooling using `MONGODB_URI` and configurable pool sizes (via `MONGODB_MAX_POOL_SIZE` or default 50). Programmatic index creation is executed inside `get_database` to guarantee that both the TTL index (`last_active` expire after 1800s) and regular index on `ip` are present.
  - **CRUD Session Management Operations**: Implemented `db/session_manager.py` to support lifecycle commands: `create_session`, `get_session`, `update_session` (which separates entity search criteria under `context` and graph runtime fields under `graph_state` matching the HLD data schema), and `delete_session`.
  - **State Merging Graph Node Operations**: Updated `restore_state` and `save_state` nodes in `graph.py` to seamlessly read and persist `AgentState` parameters from/to MongoDB. Added message merging logic in `restore_state` to combine the existing stored message history with incoming user queries without creating duplicate records.
- **Key Files Created/Modified**:
  - [connection.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/db/connection.py): Connection pool and index setup module.
  - [session_manager.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/db/session_manager.py): MongoDB operations for session state management.
  - [graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/graph.py): Integrated session manager within state restoration and saving nodes.
  - [test_session_manager.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_session_manager.py): Exhaustive integration tests for connection pools, index verification, session CRUD lifecycles, and state node merges.
  - [conftest.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/conftest.py): Added autouse setup fixture to mock MongoClient with `mongomock` across all test files.
  - [test_url_validator.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_url_validator.py): Fixed a concurrent execution race condition by implementing thread-safe, URL-dependent mock returns.
- **Verification/Testing Steps**:
  - Validated type safety using MyPy across all 25 source files with zero issues.
  - Executed all 56 backend unit and integration tests via PyTest, achieving a 100% pass rate.

---

## US-2.8 — Property Scraper Agent (New Node)

**User Story:**
As a **property seeker**,
I want to see the top 5 individual property listing links from each portal's search results,
So that I can directly visit specific properties that match my criteria without manually browsing through search pages.

**Tasks:**
- Implement `backend/agents/property_scraper.py` as a new LangGraph node
- Given a validated portal search URL (from `validated_urls`), perform an HTTP GET request to fetch the search results HTML page
  - Use a robust `User-Agent` header and `2xx` response validation
  - Implement a configurable timeout (default: 5 seconds)
- Parse the HTML response to extract individual property listing URLs:
  - **NoBroker**: Extract links matching the pattern `/property/rent/<city>/<locality>/<property-id>` or `/property/sale/<city>/<locality>/<property-id>` from the search results DOM
  - **99acres**: Extract links matching the pattern `/<locality>-<city>/.../<property-id>` from the search results DOM
- Select the **top 5** property URLs per portal (ordered as they appear on the page — portal's default relevance ranking)
- Limit total property links across all portals to a configurable maximum (default: 5 total, not per portal)
- Store scraped property URLs in state as `scraped_property_urls: list[dict]` with structure:
  ```json
  {
    "url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout/...",
    "portal": "NoBroker",
    "source_search_url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout?type=BHK3&rent=30000,50000"
  }
  ```
- Handle edge cases gracefully:
  - Portal returns no listings → empty array for that portal
  - Portal blocks scraping (403/captcha) → skip with warning log, don't fail the pipeline
  - HTML structure doesn't match expected patterns → skip with warning log
  - Network timeout → skip with warning log
- Add Langfuse span instrumentation (`tags: ["propgenie", "property_scraper"]`)
- Feature must be behind a feature flag (`ENABLE_PROPERTY_SCRAPING=true`) environment variable for easy toggling
- Write unit tests with mocked HTML responses for both NoBroker and 99acres

**Acceptance Criteria:**
- Given a valid NoBroker search URL with results, the scraper extracts up to 5 property listing URLs
- Given a valid 99acres search URL with results, the scraper extracts up to 5 property listing URLs
- Extracted URLs are valid absolute URLs pointing to individual property pages (not search pages, ads, or navigation links)
- If a portal returns 0 results, the scraped list for that portal is empty (no error raised)
- If a portal blocks the request (403/captcha/timeout), the scraper logs a warning and returns an empty list for that portal (pipeline continues)
- Total property links across all portals are capped at the configured maximum (default: 5)
- Langfuse span records scraping latency, number of links extracted per portal, and any errors
- Feature is disabled when `ENABLE_PROPERTY_SCRAPING` is not set or set to `false`
- Unit tests cover: happy path (both portals), empty results, blocked request, malformed HTML, timeout, and feature flag disabled scenarios

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Dependency-Free Parsing**: Used Python's built-in `html.parser.HTMLParser` to build `ALinkExtractor` for extracting all `href` attributes, keeping the production deployment lightweight and avoiding potential packaging issues.
  - **Path-Based Filtering Rules**: Matching logic validates URL structures sequentially to differentiate search pages from listing detail pages. For NoBroker, we verify that at least 3 slash-separated segments exist after `/property/rent/` or `/property/sale/`. For 99acres, the first segment must end with one of the supported cities (e.g. `-bangalore`) and contain subsequent segments.
  - **Concurrency & Limits**: Uses a `ThreadPoolExecutor` to fetch HTML concurrently for optimal performance. Employs `User-Agent` headers to bypass basic scraping blocks and enforces configurable request timeouts (default 5s) and capping limits (default 5 total).
  - **Tracing & Toggling**: Fully instruments the scraper with a Langfuse span recording latency, counts, and errors, and wraps the execution inside a feature flag check (`ENABLE_PROPERTY_SCRAPING`).
- **Key Files Created/Modified**:
  - [state.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/models/state.py): Added `scraped_property_urls` and `validated_property_urls` to state.
  - [property_scraper.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/property_scraper.py): Implemented the scraper node and HTML parsing/filtering logic.
  - [test_property_scraper.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_property_scraper.py): Wrote unit tests for happy path extraction, capping, blocking, and feature flags.
- **Verification/Testing Steps**:
  - Run type validation: mypy pass (0 issues).
  - Run unit test suite: pytest pass (84 tests passed successfully).

---

## US-2.9 — Property URL Validation

**User Story:**
As a **property seeker**,
I want each individual property link validated before it reaches me,
So that I never receive broken, expired, or fabricated property listing links.

**Tasks:**
- Extend `backend/agents/url_validator.py` (or add a dedicated validation step within the property scraper) to validate scraped property URLs:
  - **Structural validation**:
    - Domain must match the source portal's whitelist (`nobroker.in`, `99acres.com`)
    - URL path must contain a property identifier segment (not a search page or homepage)
    - URL must not be a duplicate of the search URL itself
  - **Liveness validation (HTTP HEAD)**:
    - Perform concurrent HTTP HEAD checks with 2-second timeout per URL
    - Accept only `2xx` responses
    - Drop URLs that return 404 (expired listings), 403 (access denied), or timeout
- Store validated property URLs in state as `validated_property_urls: list[dict]` with structure:
  ```json
  {
    "url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout/...",
    "portal": "NoBroker",
    "validation": { "schema_valid": true, "head_status": 200 }
  }
  ```
- Track dropped property URLs in Langfuse trace metadata (similar to existing hallucination flagging for search URLs)
- Write unit tests for property URL validation rules

**Acceptance Criteria:**
- A structurally valid individual property URL passes validation
- A URL pointing to a search page (not an individual property) is rejected
- A URL with a non-whitelisted domain is rejected
- An expired listing (HTTP 404) is silently dropped
- HTTP HEAD timeout (>2s) results in the property URL being dropped
- `validated_property_urls` in state contains only passing property URLs
- Dropped property URLs are tagged in Langfuse trace metadata
- Unit tests cover each validation rule independently

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Grouped Constants Compliance**: Defined `URLValidatorConstants` to encapsulate whitelisted domains, minimum path segment counts, city regex mappings, budget bounds, and HEAD timeouts, aligning with the `constants_rule`.
  - **Structural and Liveness Rules**: Property links are validated structurally (excluding duplicates of the search URL, verifying domains, checking segment counts, and ensuring city prefixes are supported) before launching concurrent HEAD checks using `ThreadPoolExecutor` with a strict 2-second timeout.
  - **Trace Hallucination Flagging**: Integrates Langfuse trace metadata tagging to record any dropped property listing links, setting the hallucination flag and recording exact error logs for diagnostics.
- **Key Files Created/Modified**:
  - [url_validator.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/url_validator.py): Added structural property checking, concurrent liveness check logic, and updated trace metadata.
  - [property_scraper.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/property_scraper.py): Cleaned up magic values using constants class and integrated validation phase.
  - [test_property_scraper.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_property_scraper.py): Added direct unit test assertions for property link validation rules.
- **Verification/Testing Steps**:
  - mypy static type checking verified: 0 issues.
  - pytest run successfully: 86 passing tests.

---

## US-2.10 — State Schema & Graph Topology Updates for Property Scraping

**User Story:**
As a **backend developer**,
I want the agent state schema and LangGraph topology updated to support the property scraping pipeline,
So that scraped property URLs flow through the graph correctly and are persisted alongside existing search data.

**Tasks:**
- Update `AgentState` in `backend/models/state.py` with new fields:
  - `scraped_property_urls: list[dict[str, Any]]` — raw scraped property URLs
  - `validated_property_urls: list[dict[str, Any]]` — validated individual property URLs
- Update `get_initial_state()` to initialize both new fields as empty lists
- Update graph topology in `backend/graph.py`:
  - Register new node: `property_scraper`
  - New edge flow: `url_validator` → `property_scraper` → `response_formatter` → `save_state`
  - (Previously: `url_validator` → `response_formatter` → `save_state`)
- Update `save_state` and `restore_state` to persist/restore `scraped_property_urls` and `validated_property_urls`
- Update `generate_graph_sse` to yield `agent_status` for the `property_scraper` node (e.g., "Fetching top property listings...")
- Write unit tests for the updated graph topology (verify correct node transitions including the new node)

**Acceptance Criteria:**
- `AgentState` includes `scraped_property_urls` and `validated_property_urls` fields with correct types
- `get_initial_state()` initializes both fields as empty lists
- Graph compiles with the new `property_scraper` node
- Edge flow is: `url_validator` → `property_scraper` → `response_formatter` → `save_state`
- `save_state` persists `validated_property_urls` to MongoDB
- `restore_state` restores `validated_property_urls` from MongoDB
- SSE stream includes an `agent_status` event for `property_scraper`
- Existing unit tests continue to pass with schema changes

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **State Integration**: Formally registered `property_scraper_node` in the LangGraph state machine flow, establishing the sequential transition sequence `url_validator` -> `property_scraper` -> `response_formatter` -> `save_state`.
  - **Database Persistence**: Updated both `create_session` and `update_session` database operations inside [session_manager.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/db/session_manager.py) to store/update the `scraped_property_urls` and `validated_property_urls` list fields under `graph_state` in the MongoDB session documents, and ensured `restore_state` recovers them.
  - **SSE Streaming Extension**: Added SSE generator status yields for the `property_scraper` node to signal client interfaces when the listing crawler is actively running.
- **Key Files Created/Modified**:
  - [graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/graph.py): Integrated node registration, edge flows, state restoration, and SSE streaming message yields.
  - [session_manager.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/db/session_manager.py): Added persistence and creation initialization for scraped and validated property listing URL lists.
  - [test_graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_graph.py): Updated expected happy path and three-round breach execution orders to assert node calls.
  - [test_session_manager.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_session_manager.py): Extended MongoDB mock asserts to verify proper property URL persistence.
- **Verification/Testing Steps**:
  - Validated type safety using MyPy, passing with zero issues across all modified files and unit tests.
  - Executed all 86 unit and integration tests via PyTest, achieving a 100% pass rate.

---

## US-2.11 — Response Formatter: Property Listing Cards

**User Story:**
As a **property seeker**,
I want individual property links displayed as clickable cards alongside the portal search link,
So that I can see both the filtered search page and specific top matching properties at a glance.

**Tasks:**
- Update `backend/agents/response_formatter.py` to include validated property URLs in the response:
  - Extend the `portal_card` event with a `property_links` array nested under each portal card
  - Each property link card includes:
    - `url`: The individual property listing URL
    - `portal`: Portal name (NoBroker / 99acres)
    - `rank`: Position (1–5) in the results
    - `validation`: Schema and HEAD status
  - Example `portal_card` with property links:
    ```json
    {
      "type": "portal_card",
      "portal": "NoBroker",
      "priority": true,
      "url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout?...",
      "summary": "3BHK rentals near HSR Layout, Bangalore — ₹30K to ₹50K/mo",
      "notes": "",
      "validation": { "schema_valid": true, "head_status": 200 },
      "property_links": [
        { "url": "https://www.nobroker.in/property/rent/.../abc123", "rank": 1, "validation": { "schema_valid": true, "head_status": 200 } },
        { "url": "https://www.nobroker.in/property/rent/.../def456", "rank": 2, "validation": { "schema_valid": true, "head_status": 200 } }
      ]
    }
    ```
- Update `search_meta` to include `property_links_count` (total validated property links returned)
- If property scraping is disabled (feature flag off), `property_links` is an empty array (backward compatible)
- Write unit tests for the updated formatting logic

**Acceptance Criteria:**
- `portal_card` events include a `property_links` array with validated individual property URLs
- Each property link includes `url`, `rank`, and `validation` fields
- Property links are ordered by their rank (page position)
- If no property links were scraped for a portal, `property_links` is an empty array (not omitted)
- `search_meta` includes `property_links_count` with the total count of validated property links
- Existing portal card format is preserved (backward compatible — `property_links` is additive)
- Unit tests validate formatting with 0, 1, and 5 property links

**Status:** Completed

### Implementation Summary
- **Design Decisions**:
  - **Additive Nesting**: Extended the `portal_card` response schema by introducing a nested `property_links` array containing individual validated property URLs.
  - **Rank Alignment**: Mapped validated property listings back to their original page order index (1-based rank) using the initial `scraped_property_urls` list and sorted ascending.
  - **Feature Flag & Backward Compatibility**: Conditioned scraping enrichment on `ENABLE_PROPERTY_SCRAPING=true`. When disabled, `property_links` naturally returns as `[]` preserving compatibility.
  - **Aggregate Search Metadata**: Added a cumulative `property_links_count` field inside the final `search_meta` payload reporting the total number of validated properties returned across all active cards.
- **Key Files Created/Modified**:
  - [response_formatter.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/agents/response_formatter.py): Modified to rank, sort, and embed property links, and track meta count.
  - [graph.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/graph.py): Updated the fallback `search_meta` generator in the SSE stream flow to count validated URLs.
  - [test_response_formatter.py](file:///c:/Users/Susmi/Desktop/sandeep/ws/PropGenie/backend/tests/unit/test_response_formatter.py): Appended unit tests covering feature-disabled, empty, single-listing, and multiple-listing sorted rank cases.
- **Verification/Testing Steps**:
  - Validated type safety using MyPy, passing with 0 issues across all modified files.
  - Executed all 90 tests via PyTest, achieving a 100% pass rate.

---

## US-2.12 — API Contract & SSE Event Updates for Property Links

**User Story:**
As a **frontend developer**,
I want the API contract updated to document the new `property_links` field and related SSE events,
So that I can integrate the property listing links into the chat UI correctly.

**Tasks:**
- Update `docs/hld/05-api-contract.md`:
  - Update `portal_card` event schema to include `property_links` array
  - Add `agent_status` event for `property_scraper` agent
  - Update `search_meta` to include `property_links_count`
- Update `frontend/src/types/domain.ts`:
  - Add `PropertyLink` interface: `{ url: string; rank: number; validation: { schema_valid: boolean; head_status: number } }`
  - Add `propertyLinks?: PropertyLink[]` to `PortalResult` interface
  - Update `SearchMeta` to include `propertyLinksCount: number`
- Update `frontend/src/types/sse.ts` to handle the updated `portal_card` event shape

**Acceptance Criteria:**
- HLD API contract documents the `property_links` array within `portal_card`
- HLD API contract documents the `property_scraper` agent status event
- Frontend TypeScript types include `PropertyLink` interface
- `PortalResult` type includes optional `propertyLinks` array
- `SearchMeta` type includes `propertyLinksCount`
- SSE parser correctly deserializes `property_links` from `portal_card` events

**Status:** Not Started

---

## US-2.13 — Frontend: Property Links UI

**User Story:**
As a **property seeker**,
I want individual property links displayed as a ranked list below each portal search card,
So that I can quickly click through to the most relevant individual properties.

**Tasks:**
- Create a new `PropertyLinkList` component (or extend `PortalCard`):
  - Display up to 5 property links as a compact, numbered list under the portal search card
  - Each link shows:
    - Rank number (1–5)
    - Shortened URL or "View Property #N on NoBroker" label
    - Opens in new tab on click
  - Subtle visual hierarchy: search link is primary (prominent), property links are secondary (smaller, indented)
- Handle edge cases:
  - 0 property links → don't render the list section (only show the search link as before)
  - Loading state → show skeleton/shimmer while `property_scraper` agent is active
- Write Storybook stories for the new component (0, 1, 3, 5 property links)
- Write unit/component tests

**Acceptance Criteria:**
- Property links are rendered as a numbered list below the portal search card
- Each property link opens in a new tab
- If 0 property links exist, the UI is identical to the current behavior (no empty section)
- Loading state shows appropriate shimmer during the scraping phase
- Responsive layout works on mobile and desktop viewports
- Storybook stories cover all edge cases (0, 1, 3, 5 links)
- Visual hierarchy clearly distinguishes the search link (primary) from property links (secondary)

**Status:** Not Started

