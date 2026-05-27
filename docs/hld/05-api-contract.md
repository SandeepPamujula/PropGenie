# 5. API Contract

## 5.1 Chat Endpoint

**Request:**
```
POST /api/chat
Content-Type: application/json
Accept: text/event-stream
X-Session-ID: <uuid-v4>
```

```json
{
  "message": "I want to rent a 3BHK near HSR Layout, budget 20k to 30k"
}
```

**Response:** SSE stream (`text/event-stream`). Each event:
```
event: <event_type>
data: <json_payload>

```

### Event: `agent_status`
Indicates current pipeline execution phase. Possible values for `agent` are `"orchestrator"`, `"clarification"`, `"query_builder"`, `"url_validator"`, `"property_scraper"`, and `"response_formatter"`.

```json
{
  "type": "agent_status",
  "agent": "orchestrator",
  "message": "Understanding your search...",
  "timestamp": "2026-05-16T10:30:00Z"
}
```

### Event: `clarification`
```json
{
  "type": "clarification",
  "message": "Are you looking to buy or rent this flat?",
  "round": 1,
  "max_rounds": 3,
  "resolved_fields": {"city": "Bangalore", "property_type": "flat"},
  "missing_fields": ["intent", "budget", "bhk"]
}
```

### Event: `portal_card`
```json
{
  "type": "portal_card",
  "portal": "NoBroker",
  "priority": true,
  "url": "https://www.nobroker.in/property/residential/rent/bangalore/...",
  "summary": "3BHK rentals near HSR Layout, Bangalore — ₹20K to ₹30K/mo",
  "notes": "4 km radius applied around HSR Layout",
  "validation": {"schema_valid": true, "head_status": 200},
  "property_links": [
    {
      "url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout/abc123",
      "portal": "NoBroker",
      "rank": 1,
      "validation": {"schema_valid": true, "head_status": 200}
    }
  ]
}
```

### Event: `search_meta`
```json
{
  "type": "search_meta",
  "portals_searched": 2,
  "portals_returned": 2,
  "portals_dropped": [],
  "property_links_count": 1,
  "clarification_rounds": 0,
  "defaults_applied": ["radius_km: 4"]
}
```

### Event: `error`
```json
{
  "type": "error",
  "message": "I'm having trouble connecting right now. Please try again in a moment.",
  "retryable": true
}
```

### Event: `done`
```json
{
  "type": "done",
  "session_id": "abc-123-def",
  "search_count_today": 3,
  "search_limit": 10
}
```

## 5.2 Rate Limit Response (non-SSE)

Returned directly by the Lambda handler when the rate limit is exceeded (before the agent graph is invoked):

```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
```
```json
{
  "error": "rate_limit_exceeded",
  "message": "You've reached your daily search limit of 10. Please try again tomorrow!",
  "reset_at": "2026-05-17T00:00:00+05:30"
}
```

## 5.3 Health Endpoint

```
GET /api/health → 200 OK
```
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-16T10:30:00Z"
}
```
