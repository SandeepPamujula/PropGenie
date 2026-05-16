# 2. System Architecture

## 2.1 System Context Diagram (C4 Level 1)

```mermaid
C4Context
    title PropGenie — System Context (C4 Level 1)

    Person(user, "Property Seeker", "Searches for properties to buy or rent in India via chat")

    System(propgenie, "PropGenie", "Conversational AI property search assistant")

    System_Ext(bedrock, "AWS Bedrock", "Llama 3.1 70B Instruct LLM")
    System_Ext(portals, "Real Estate Portals", "NoBroker, 99acres")
    System_Ext(mongodb, "MongoDB Atlas", "Session state, rate limits, search logs")
    System_Ext(langfuse, "Langfuse Cloud", "LLM observability and tracing")

    Rel(user, propgenie, "Chats via browser", "HTTPS / SSE")
    Rel(propgenie, bedrock, "LLM inference", "AWS SDK")
    Rel(propgenie, portals, "HTTP HEAD validation", "HTTPS")
    Rel(propgenie, mongodb, "Read/write state", "MongoDB driver")
    Rel(propgenie, langfuse, "Sends traces", "HTTPS")
```

## 2.2 Container Diagram (C4 Level 2)

```mermaid
C4Container
    title PropGenie — Container Diagram (C4 Level 2)

    Person(user, "Property Seeker")

    Container_Boundary(aws, "AWS Cloud") {
        Container(cdn, "CloudFront", "CDN", "Serves static frontend, routes /api/* to Lambda, extracts CloudFront-Viewer-Address IP")
        Container(s3, "S3 Bucket", "Static Hosting", "Next.js static export assets")
        Container(agent_fn, "PropGenie Agent", "Lambda Function URL (Python)", "Monolithic LangGraph graph — Orchestrator, Clarification, QueryBuilder, URLValidator, Formatter. Includes inline rate limiting")
        Container(cw, "CloudWatch", "Monitoring", "Logs, metrics, alarms")
    }

    System_Ext(bedrock, "AWS Bedrock", "Llama 3.1 70B Instruct")
    System_Ext(mongodb, "MongoDB Atlas", "Sessions, rate_limits, search_logs")
    System_Ext(langfuse, "Langfuse Cloud", "LLM tracing")
    System_Ext(portals, "Real Estate Portals", "NoBroker, 99acres")

    Rel(user, cdn, "HTTPS")
    Rel(cdn, s3, "Origin fetch")
    Rel(cdn, agent_fn, "/api/* requests", "Lambda Function URL origin")
    Rel(agent_fn, bedrock, "LLM calls")
    Rel(agent_fn, mongodb, "Session CRUD, rate limits, search logs")
    Rel(agent_fn, portals, "HTTP HEAD validation")
    Rel(agent_fn, langfuse, "Trace spans")
    Rel(agent_fn, cw, "Logs & metrics")
```

## 2.3 Request Flow

```
┌──────────┐     HTTPS      ┌────────────┐    Origin     ┌─────┐
│  Browser  │──────────────►│ CloudFront  │─────────────►│ S3  │  (static assets)
│ (Next.js) │               │  (CDN)      │              └─────┘
│           │               │             │
│           │   /api/chat   │  Viewer-    │    ┌──────────────────────┐
│           │──────────────►│  Address    │──►│  PropGenie Agent      │
└──────────┘               └────────────┘    │  Lambda Function URL  │
                                              │  (LangGraph graph)    │
                                              └──────────┬────────────┘
                                                         │
                                          ┌──────────────┼──────────────┐
                                          │              │              │
                                          ▼              ▼              ▼
                                       Bedrock       MongoDB       Portals
                                       (LLM)        (state)     (HEAD check)
```

**Flow summary:**
1. Browser sends `POST /api/chat` with `X-Session-ID` header and user message body
2. CloudFront forwards to Lambda Function URL origin, injecting `CloudFront-Viewer-Address` header
3. Lambda handler extracts IP from `CloudFront-Viewer-Address`, checks rate limit in MongoDB `rate_limits`
4. If rate limit exceeded, returns 429 JSON response immediately
5. If allowed, invokes the LangGraph agent graph
6. Agent Lambda streams SSE events back to the browser via Lambda Function URL response streaming
7. On search completion, the agent increments the rate limit counter and logs the search

## 2.4 Agent Interaction — LangGraph Graph Topology

```mermaid
stateDiagram-v2
    [*] --> RestoreState: New message arrives
    RestoreState --> RateLimitCheck: Load session from MongoDB

    RateLimitCheck --> Orchestrator: Under limit
    RateLimitCheck --> RateLimitDenied: Limit exceeded (429)
    RateLimitDenied --> [*]: Return 429 response

    Orchestrator --> Clarification: Missing/ambiguous fields
    Orchestrator --> QueryBuilder: All fields resolved

    Clarification --> StreamResponse: Emit clarification question
    StreamResponse --> SaveState: Save graph state to MongoDB
    SaveState --> [*]: Return SSE stream to user

    QueryBuilder --> URLValidator: URLs generated
    URLValidator --> ResponseFormatter: Valid URLs
    URLValidator --> ResponseFormatter: Some URLs dropped

    ResponseFormatter --> StreamResponse2: Emit portal cards
    StreamResponse2 --> LogSearch: Write to search_logs
    LogSearch --> IncrementRateLimit: Increment IP counter
    IncrementRateLimit --> SaveState2: Save final state
    SaveState2 --> [*]: Return SSE stream to user
```

**Graph nodes (all run in a single Lambda invocation):**

| Node | Purpose | LLM call? |
|------|---------|-----------|
| `restore_state` | Load session from MongoDB, rehydrate LangGraph state | No |
| `rate_limit_check` | Check IP rate limit in MongoDB, reject if exceeded | No |
| `orchestrator` | Intent classification, entity extraction, completeness check | Yes |
| `clarification` | Generate one clarifying question | Yes |
| `query_builder` | Build portal-specific deep-link URLs | Yes (for location mapping) |
| `url_validator` | Validate URLs structurally + HTTP HEAD | No |
| `response_formatter` | Format portal cards for SSE output | No (template-based) |
| `save_state` | Persist graph state + session to MongoDB | No |
