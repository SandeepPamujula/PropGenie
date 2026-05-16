# AI Agent Architecture Prompt: Property Search Assistant (v1 — Final)

## Role & Objective

You are a **Senior AI Architect** designing a production-ready, agentic AI system for a conversational property search assistant. Users interact via a chat window to find properties to **buy or rent** anywhere in India, receiving curated deep-link search URLs from major Indian real estate portals. The system uses a multi-agent architecture orchestrated by LangGraph on AWS Lambda, powered by AWS Bedrock (Claude 3.5 Sonnet), with MongoDB Atlas for persistence and Langfuse + CloudWatch for observability.

---

## Tech Stack (Locked)

| Layer | Technology |
|---|---|
| Frontend | Next.js (static export, no SSR). **CRITICAL RULE:** Do not create a `src/app/api` directory, to avoid routing conflicts with CloudFront `/api/*`. |
| Frontend hosting | S3 + CloudFront (default domain, v1) |
| Streaming | Server-Sent Events (SSE), token-by-token |
| API layer | AWS API Gateway (HTTP API) |
| Backend runtime | Python on AWS Lambda |
| Agent orchestration | LangGraph |
| LLM | AWS Bedrock — Claude 3.5 Sonnet |
| Database | MongoDB Atlas |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| LLM observability | Langfuse + AWS CloudWatch |
| Environments | dev + prod |

---

## Functional Requirements

### Core Use Cases (Representative, Not Exhaustive)

| Intent | Location anchor | Radius | Budget | Property type |
|---|---|---|---|---|
| Buy | Airport Road Metro Station, Bangalore | 5 km | ₹1Cr – ₹1.5Cr | Plot |
| Buy | Manyata Tech Park, Bangalore | unspecified | ₹1.5Cr – ₹2Cr | House |
| Rent | NPS School, Indiranagar, Bangalore | unspecified | ₹25K – ₹35K/mo | 3BHK |
| Rent | HSR Layout, Bangalore | unspecified | ₹20K – ₹30K/mo | 2BHK |

The system must support **any Indian city**, not just Bangalore.

### Portal Coverage (v1)

Deep-link URLs only — no portal API integration. Prioritized portals:

1. **NoBroker** (priority — especially for rentals)
2. **99acres** (priority — especially for purchases)
3. MagicBricks
4. Housing.com
5. Square Yards

Each portal has different query parameter schemas. The Query Builder Agent must maintain a **portal adapter config** (JSON/YAML) mapping normalized fields to portal-specific URL parameters, making it trivial to add new portals.

---

## Agent Architecture

### Orchestrator Agent (LangGraph Supervisor Node)

The central state machine controller. Every user message enters here.

**Responsibilities:**
- Intent classification: `Buy | Rent | Ambiguous`
- Entity extraction: location anchor, city, budget range, BHK, property type, radius preference
- Completeness check against required fields for the classified intent
- Enforce clarification round limit (max 3 rounds)
- Route to Clarification Agent if fields are missing, or to Query Builder Agent if complete
- Delegate rate limit enforcement to the API Gateway middleware — not handled within the agent itself
- Maintain reference to current session state via Session State Manager

**Required fields by intent:**

| Field | Buy (plot/house) | Rent |
|---|---|---|
| Intent | ✓ | ✓ |
| Location anchor | ✓ | ✓ |
| City | ✓ | ✓ |
| Property type | ✓ | ✓ |
| Budget range | ✓ | ✓ |
| BHK | not required | ✓ |
| Radius | default 4 km | default 4 km |
| Budget floor | default ₹0 / ₹0/mo | default ₹0/mo |

### Clarification Agent

Generates a single, contextual, conversational clarifying question when required fields are missing or ambiguous.

**Behaviors:**
- Receives list of missing/ambiguous fields from the Orchestrator
- Asks **exactly one question per turn** — never a form dump
- Maintains conversational, friendly tone (not robotic)
- After 3 clarification rounds without resolution, signals the Orchestrator to proceed with best-effort defaults and perform the search
- Language: English only (v1)

**Clarification triggers (ask if any of these are missing or ambiguous):**
- Intent (buy vs rent)
- Location or city unclear / missing
- Budget missing or expressed vaguely (e.g. "affordable")
- Property type not specified (plot / apartment / villa / independent house)
- BHK not specified (rentals only)
- Radius preference (only ask if user's location anchor is a point of interest like a metro station; otherwise apply 4 km default silently)

**Do not ask about:**
- Furnishing level (optional, v1)
- Floor preference, age of property, amenities (v2+)

### Query Builder Agent

Translates a fully resolved intent + entity set into portal-specific deep-link search URLs.

**Behaviors:**
- Applies defaults before building URLs: radius = 4 km if not specified, budget floor = ₹0/₹0 per month if not specified
- Maps location anchor to portal-understood locality names or lat/lng bounding box
- Builds parameterized URLs for all 5 portals; returns them as a structured list with portal name and metadata
- Passes URL list to the URL Validator Agent before returning to formatter

**Portal adapter config structure (per portal):**
```yaml
portal_id: nobroker
base_url: https://www.nobroker.in/property/residential/
params:
  intent: { buy: "sale", rent: "rent" }
  city: city_slug_map
  locality: locality_param
  budget_min: minAmount
  budget_max: maxAmount
  bhk: noOfBedrooms
  property_type: propertyType
```

### URL Validator Agent

Validates all generated URLs against known portal schema rules before they are returned to the user. This is the primary defense against the hallucination risk of fabricated portal links or locality names.

**Validation rules:**
- Base domain must match the known portal domain (whitelist)
- Required query parameters for each portal must be present and non-empty
- Budget values must be numeric and within plausible range (₹1K – ₹50Cr for buy; ₹1K – ₹5L/mo for rent)
- Locality/city strings must not be empty
- If a URL fails validation, it is dropped silently — not returned to the user
- If all URLs for a portal fail, that portal is excluded from the response with no mention to the user

### Response Formatter Agent

Formats the validated URL list into a structured response streamed token-by-token to the frontend via SSE.

**Output format per portal card:**
- Portal name + priority indicator (if NoBroker or 99acres)
- One-line human-readable search summary (e.g. "3BHK rentals near HSR Layout, Bangalore — ₹20K to ₹30K/mo")
- Direct deep-link URL
- Brief note if radius was defaulted or budget floor was assumed

---

## Non-Functional Requirements

### Rate Limiting

- **Limit:** 10 searches per IP per calendar day (resets at midnight IST)
- **What counts as a search:** A successful invocation of the Query Builder Agent — i.e. all required fields resolved and URLs generated. Clarification exchanges do **not** count.
- **Enforcement:** Lambda authorizer at API Gateway checks IP count in MongoDB `rate_limits` collection before routing the request
- **On limit breach:** Return a friendly message: the user's daily limit has been reached; they can try again tomorrow
- **Storage:** `rate_limits` collection — fields: `ip`, `count`, `date` (YYYY-MM-DD IST), TTL index on `date` (auto-expire after 2 days)

### Conversation & Session

- Session ID generated client-side (UUID v4), sent as a header on every request
- Session document stored in MongoDB `sessions` collection
- Session expires after 30 minutes of inactivity (TTL index on `last_active`)
- On session expiry, user starts a fresh conversation — context is not carried across sessions

### Streaming

- Responses stream token-by-token from Lambda to frontend via SSE (`text/event-stream`)
- LangGraph emits agent state transitions as stream events — the frontend may render intermediate states (e.g. "Searching NoBroker…") before the final card list arrives

---

## Data Architecture (MongoDB Atlas)

### `sessions` collection
```json
{
  "_id": "session_uuid",
  "ip": "x.x.x.x",
  "context": {
    "intent": "rent",
    "city": "Bangalore",
    "bhk": 3,
    "budget_max": 35000,
    "location": "NPS Indiranagar",
    "radius_km": 4
  },
  "clarification_round": 1,
  "last_active": "ISODate",
  "created_at": "ISODate"
}
```
TTL index on `last_active` (expire after 1800 seconds).

### `rate_limits` collection
```json
{
  "_id": "ip_date_composite",
  "ip": "x.x.x.x",
  "date": "2024-01-15",
  "count": 4
}
```
TTL index on `date` (expire after 2 days).

### `search_logs` collection (analytics, retained indefinitely)
```json
{
  "_id": "log_uuid",
  "session_id": "session_uuid",
  "ip_hash": "sha256_of_ip",
  "intent": "rent",
  "city": "Bangalore",
  "location_anchor": "NPS Indiranagar",
  "property_type": "house",
  "bhk": 3,
  "budget_min": 25000,
  "budget_max": 35000,
  "radius_km": 4,
  "portals_returned": ["nobroker", "99acres", "magicbricks"],
  "clarification_rounds": 1,
  "timestamp": "ISODate"
}
```
Note: Store `ip_hash` (SHA-256), never raw IP, in `search_logs` for privacy compliance.

---

## Observability & LLM Monitoring

### Langfuse (Primary LLM Observability)

Recommended because it is open-source-compatible, supports LangGraph tracing natively, and keeps LLM monitoring separate from infrastructure monitoring.

**Instrument every agent invocation with:**
- `trace_id` tied to `session_id`
- `span` per agent (Orchestrator, Clarification, QueryBuilder, URLValidator, Formatter)
- Per-span metrics: latency (ms), input token count, output token count, Bedrock cost estimate
- Confidence score: extracted from model's response metadata or estimated via self-consistency sampling
- Hallucination flag: set by URL Validator Agent when a generated URL fails schema validation (proxy metric for hallucination)
- Clarification round count per session (higher = lower intent clarity)

### AWS CloudWatch (Infrastructure Monitoring)

- Lambda duration, error rate, cold start count per function
- API Gateway 4xx / 5xx rates
- Rate limit breach count per day (custom metric from Lambda authorizer)
- MongoDB Atlas: connection pool utilization, query latency (via Atlas monitoring or CloudWatch sink)
- Alarms: Lambda error rate > 1%, API 5xx > 0.5%, cold starts > 10/min

---

## Conversation Flow (Canonical Happy Path)

```
User:  "I want to rent a 3BHK near NPS Indiranagar, budget 25k to 35k"

Orchestrator:
  Intent:          Rent ✓
  Property type:   House ✓
  BHK:             3 ✓
  Location:        NPS Indiranagar ✓
  City:            Bangalore (inferred) ✓
  Budget:          ₹25K – ₹35K/mo ✓
  Radius:          not specified → default 4 km (silent)
  → All fields resolved → route to Query Builder Agent

Query Builder Agent:
  → Builds URLs for NoBroker, 99acres, MagicBricks, Housing.com, Square Yards

URL Validator Agent:
  → Validates all 5 URLs against portal schema rules
  → All pass

Response Formatter Agent:
  → Streams portal cards with search summaries + direct links
  → Notes: "4 km radius applied around NPS Indiranagar"

Rate Limit Middleware:
  → Increments count for this IP in rate_limits for today
  → count: 1 of 10
```

### Clarification Path (Ambiguous Input)

```
User:  "looking for a flat in bangalore"

Orchestrator:
  Intent:    Ambiguous (buy or rent?) → missing
  → Route to Clarification Agent (round 1 of 3)

Clarification Agent:
  → "Are you looking to buy or rent this flat?"

User:  "rent"

Orchestrator:
  Intent:    Rent ✓
  BHK:       missing
  → Route to Clarification Agent (round 2 of 3)

Clarification Agent:
  → "How many bedrooms are you looking for — 1BHK, 2BHK, or 3BHK?"

User:  "2bhk, budget 20k to 30k, near HSR Layout"

Orchestrator:
  BHK:       2 ✓
  Budget:    ₹20K–₹30K ✓
  Location:  HSR Layout ✓
  → All fields resolved → route to Query Builder Agent
  → Note: clarification_rounds = 2, logged to search_logs
```

### 3-Round Breach Path

```
After 3 rounds with budget still unresolved:

Orchestrator:
  → Clarification limit reached
  → Apply defaults: budget_min = ₹0, budget_max = unlimited
  → Route to Query Builder Agent with best-effort values

Response Formatter Agent:
  → Streams results with note:
     "I've searched broadly since a budget wasn't specified —
      you can refine by telling me your preferred range."
```

---

## Infrastructure as Code (Terraform)

Resources to define:
- S3 bucket (static frontend assets) + bucket policy
- CloudFront distribution (S3 origin, default cache behavior, HTTPS)
- API Gateway HTTP API + routes + Lambda integrations
- Lambda functions: Orchestrator, Clarification, QueryBuilder, URLValidator, Formatter, RateLimitAuthorizer
- Lambda IAM roles (least-privilege: Bedrock invoke, MongoDB Atlas network access, CloudWatch logs)
- AWS WAF WebACL attached to API Gateway
- CloudWatch log groups, metric filters, alarms
- SSM Parameter Store entries for MongoDB Atlas connection string, Langfuse API key, Bedrock region

Terraform workspaces: `dev` and `prod`. Variable files per workspace. State stored in S3 backend with DynamoDB lock table.

---

## CI/CD (GitHub Actions)

### Pipelines

**Feature branch (`feature/*`):**
1. Lint (ESLint for Next.js, Ruff for Python)
2. Unit tests (pytest, Jest)
3. Terraform plan (dev workspace)

**Main branch merge:**
1. All above
2. Terraform apply (dev workspace)
3. Next.js build → S3 sync (dev bucket)
4. CloudFront cache invalidation (dev distribution)

**Release / manual trigger (prod):**
1. Terraform apply (prod workspace)
2. Next.js build → S3 sync (prod bucket)
3. CloudFront cache invalidation (prod distribution)
4. Smoke test: hit `/health` endpoint, assert 200

### Secrets Management

All secrets (MongoDB URI, Langfuse key, Bedrock credentials) stored in GitHub Actions secrets → injected as environment variables in Lambda via SSM Parameter Store at deploy time.

---

## V2 Considerations (Out of Scope for v1)

- Migrate LangGraph Lambda functions to Kubernetes (EKS) if traffic demands horizontal scaling beyond Lambda concurrency limits
- Add authentication (Cognito or Auth0) — rate limiting migrates from IP-based to user-based
- Hindi and regional language support via Bedrock translation layer before Orchestrator
- Portal API integrations (if portals offer partner access) for live listing counts
- Personalization: remember user preferences across sessions (requires auth)
- Map view: embed a geo search UI alongside portal links

## The HLD output section would instruct the design tool to produce:
### Diagrams
- System context diagram (C4 Level 1) — PropGenie and its external dependencies
- Container diagram (C4 Level 2) — Frontend, API Gateway, Lambda functions, MongoDB, Bedrock, Langfuse
- Agent interaction sequence diagram — message flow across all 5 agents for the happy path and clarification path
- Data flow diagram — how a user query moves from chat input to portal URL response
- CI/CD pipeline diagram — GitHub Actions stages for dev and prod

### Written sections
- Executive summary (2–3 paragraphs, non-technical)
- Component inventory table — name, type, responsibility, technology
- Agent responsibility matrix — which agent owns which decision
- API contract — request/response shape for the chat endpoint
- Data schema definitions — the 3 MongoDB collections
- Non-functional requirements summary — rate limiting, session, streaming, observability
- Risk & mitigation table — top 5 risks (portal schema drift, Lambda cold starts, IP spoofing, LLM hallucination, rate limit bypass)
- V2 roadmap section

### Delivery format
Diagrams as editable files (Mermaid, Draw.io XML, or Figma-compatible)
Written sections as a structured Markdown or Confluence-ready document
