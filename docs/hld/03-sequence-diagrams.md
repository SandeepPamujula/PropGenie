# 3. Sequence Diagrams

## 3.1 Happy Path — All Fields Resolved in First Message

```mermaid
sequenceDiagram
    actor User
    participant FE as Next.js Frontend
    participant CF as CloudFront
    participant Agent as PropGenie Agent Lambda
    participant DB as MongoDB Atlas
    participant LLM as Bedrock (Llama 3.1 70B)
    participant Portals as Real Estate Portals
    participant LF as Langfuse Cloud

    User->>FE: "Rent 3BHK near HSR Layout, 20k-30k"
    FE->>CF: POST /api/chat {session_id, message}
    CF->>Agent: Forward to Function URL + CloudFront-Viewer-Address header

    Note over Agent: Rate limit check
    Agent->>DB: Query rate_limits for IP + today's date (IST)
    DB-->>Agent: {count: 2}
    Agent->>Agent: Allow (2 < 10)

    Note over Agent: restore_state node
    Agent->>DB: Load session (or create new)
    DB-->>Agent: Session state

    Note over Agent: orchestrator node
    Agent->>LLM: Classify intent + extract entities
    Agent->>LF: Span: orchestrator (latency, tokens)
    LLM-->>Agent: {intent: rent, bhk: 3, city: Bangalore, location: HSR Layout, budget: 20k-30k}
    Agent-->>FE: SSE: {type: "agent_status", message: "Understanding your search..."}

    Note over Agent: query_builder node
    Agent->>LLM: Map "HSR Layout" to portal locality slugs
    Agent->>LF: Span: query_builder
    LLM-->>Agent: Portal-specific locality mappings
    Agent->>Agent: Build 2 portal URLs from adapter config
    Agent-->>FE: SSE: {type: "agent_status", message: "Building search links..."}

    Note over Agent: url_validator node
    loop For each portal URL
        Agent->>Agent: Schema validation (domain, params)
        Agent->>Portals: HTTP HEAD request
        Portals-->>Agent: 200 OK / 404 / 301
    end
    Agent->>LF: Span: url_validator (pass/fail counts)
    Agent-->>FE: SSE: {type: "agent_status", message: "Verifying links..."}

    Note over Agent: property_scraper node
    loop For each validated search URL
        Agent->>Portals: HTTP GET request (fetch HTML results page)
        Portals-->>Agent: 200 OK HTML
        Agent->>Agent: Parse HTML, extract top 5 property listing URLs
        Agent->>Agent: Run concurrent HEAD check on listing URLs
    end
    Agent->>LF: Span: property_scraper (latency, listing counts)
    Agent-->>FE: SSE: {type: "agent_status", message: "Fetching top property listings..."}

    Note over Agent: response_formatter node
    Agent-->>FE: SSE: {type: "portal_card", portal: "NoBroker", url: "...", summary: "...", property_links: [...]}
    Agent-->>FE: SSE: {type: "portal_card", portal: "99acres", url: "...", summary: "...", property_links: [...]}
    Agent-->>FE: SSE: {type: "done"}

    Note over Agent: save_state + logging
    Agent->>DB: Save session state
    Agent->>DB: Insert search_log (ip_hash, intent, entities, portals_returned)
    Agent->>DB: Increment rate_limits count for IP
    Agent->>LF: Complete trace
```

## 3.2 Clarification Path — 2 Rounds

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant Agent as PropGenie Agent Lambda
    participant DB as MongoDB
    participant LLM as Bedrock

    User->>FE: "looking for a flat in bangalore"
    FE->>Agent: POST /api/chat (via CloudFront → Function URL)

    Note over Agent: Rate limit check → Allow
    Note over Agent: Restore state → Orchestrator
    Agent->>LLM: Classify + extract
    LLM-->>Agent: {intent: AMBIGUOUS, city: Bangalore, property_type: flat}

    Note over Agent: Clarification (round 1)
    Agent->>LLM: Generate clarification question
    LLM-->>Agent: "Are you looking to buy or rent?"
    Agent-->>FE: SSE: {type: "clarification", message: "Are you looking to buy or rent?"}
    Agent->>DB: Save state {clarification_round: 1, entities: {...}}

    User->>FE: "rent"
    FE->>Agent: POST /api/chat

    Note over Agent: Rate limit check → Allow (clarification doesn't count)
    Note over Agent: Restore state → Orchestrator
    Agent->>DB: Load state {clarification_round: 1}
    Agent->>LLM: Re-classify with new info
    LLM-->>Agent: {intent: rent, bhk: MISSING, budget: MISSING}

    Note over Agent: Clarification (round 2)
    Agent->>LLM: Generate question for BHK
    LLM-->>Agent: "How many bedrooms — 1BHK, 2BHK, or 3BHK?"
    Agent-->>FE: SSE: {type: "clarification", message: "How many bedrooms...?"}
    Agent->>DB: Save state {clarification_round: 2}

    User->>FE: "2bhk, budget 20k to 30k, near HSR Layout"
    FE->>Agent: POST /api/chat

    Note over Agent: Rate limit check → Allow
    Note over Agent: Restore state → Orchestrator
    Agent->>DB: Load state {clarification_round: 2}
    Agent->>LLM: Re-classify — all fields resolved
    
    Note over Agent: QueryBuilder → URLValidator → Formatter
    Agent->>Agent: Build URLs → Validate → Format
    Agent-->>FE: SSE: {type: "portal_card", ...} × N
    Agent-->>FE: SSE: {type: "done"}
    Agent->>DB: Save + log + increment rate limit
```

## 3.3 Rate Limit Breach Path

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant CF as CloudFront
    participant Agent as PropGenie Agent Lambda
    participant DB as MongoDB

    User->>FE: "rent 2bhk in mumbai..."
    FE->>CF: POST /api/chat
    CF->>Agent: Forward to Function URL + CloudFront-Viewer-Address
    Agent->>DB: Query rate_limits for IP
    DB-->>Agent: {count: 10}
    Agent->>Agent: Deny (10 >= 10)
    Agent-->>FE: 429 {message: "daily limit reached", reset_at: "midnight IST"}
    FE->>User: "You've reached your daily search limit. Please try again tomorrow!"
```

## 3.4 3-Round Clarification Breach — Best-Effort Fallback

```mermaid
sequenceDiagram
    actor User
    participant Agent as PropGenie Agent Lambda
    participant DB as MongoDB
    participant LLM as Bedrock

    Note over Agent: Round 3, budget still missing
    Agent->>DB: Load state {clarification_round: 3, budget: MISSING}
    Agent->>Agent: Max clarification rounds reached
    Agent->>Agent: Apply defaults (budget_min: 0, budget_max: unlimited)

    Note over Agent: QueryBuilder → URLValidator → Formatter
    Agent->>Agent: Build URLs with best-effort values
    Agent-->>User: SSE portal cards + note: "I've searched broadly since a budget wasn't specified"
    Agent->>DB: Log search with clarification_rounds: 3
```
