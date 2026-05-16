# 6. Data Schema Definitions (MongoDB Atlas)

## 6.1 `sessions` Collection

Stores conversation state and serves as the LangGraph checkpoint store.

```json
{
  "_id": "uuid-v4 (session_id)",
  "ip": "x.x.x.x",
  "context": {
    "intent": "rent | buy | null",
    "city": "Bangalore",
    "location_anchor": "HSR Layout",
    "property_type": "house | flat | plot | villa | null",
    "bhk": 3,
    "budget_min": 25000,
    "budget_max": 35000,
    "radius_km": 4
  },
  "graph_state": {
    "current_node": "orchestrator | clarification | query_builder | url_validator | response_formatter",
    "pending_fields": ["bhk", "budget"],
    "generated_urls": [],
    "validated_urls": []
  },
  "clarification_round": 1,
  "messages": [
    {"role": "user", "content": "looking for a flat in bangalore", "ts": "ISODate"},
    {"role": "assistant", "content": "Are you looking to buy or rent?", "ts": "ISODate"}
  ],
  "last_active": "ISODate",
  "created_at": "ISODate"
}
```

**Indexes:**
- `last_active`: TTL index, expire after 1800 seconds (30 min inactivity)
- `ip`: regular index for rate-limit cross-reference

## 6.2 `rate_limits` Collection

Tracks search invocations per IP per calendar day (IST).

```json
{
  "_id": "sha256(ip)_2026-05-16",
  "ip": "x.x.x.x",
  "date": "2026-05-16",
  "count": 4,
  "last_incremented": "ISODate",
  "expires_at": "ISODate (midnight IST + 2 days)"
}
```

**Indexes:**
- `expires_at`: TTL index, expire when `expires_at` is reached (MongoDB deletes documents when the ISODate value is in the past)
- `{ip, date}`: compound unique index for upsert operations

**Operations:**
- **Check:** `find({ip, date: today_IST_string})` → if `count >= 10`, deny
- **Increment:** `updateOne({ip, date: today_IST_string}, {$inc: {count: 1}, $set: {last_incremented: now, expires_at: today_IST + 2_days}}, {upsert: true})`

> **Note:** The `date` field remains a string for query convenience (IST calendar day). The `expires_at` field is an ISODate used by the TTL index for automatic cleanup (set to midnight IST of the current day + 2 days).

## 6.3 `search_logs` Collection

Analytics log for every completed search. Retained indefinitely.

```json
{
  "_id": "uuid-v4",
  "session_id": "session_uuid",
  "ip_hash": "sha256(ip)",
  "intent": "rent",
  "city": "Bangalore",
  "location_anchor": "HSR Layout",
  "property_type": "house",
  "bhk": 3,
  "budget_min": 25000,
  "budget_max": 35000,
  "radius_km": 4,
  "portals_searched": ["nobroker", "99acres"],
  "portals_returned": ["nobroker", "99acres"],
  "portals_dropped": [],
  "clarification_rounds": 1,
  "defaults_applied": ["radius_km"],
  "latency_ms": 3200,
  "llm_calls": 3,
  "total_input_tokens": 1500,
  "total_output_tokens": 800,
  "timestamp": "ISODate"
}
```

**Indexes:**
- `timestamp`: for time-range queries
- `city`: for analytics aggregation
- `intent`: for buy/rent distribution analysis

> **Privacy:** Raw IP is never stored in `search_logs`. Only `ip_hash` (SHA-256) is persisted.
