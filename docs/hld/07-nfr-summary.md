# 7. Non-Functional Requirements Summary

## 7.1 Rate Limiting

| Attribute | Value |
|-----------|-------|
| Limit | 10 search flows per IP per calendar day (IST) |
| What counts | Completed search invocations (Query Builder executes) |
| What doesn't count | Clarification exchanges |
| Enforcement | Inline check in Lambda handler, queries MongoDB before invoking graph |
| IP source | CloudFront `CloudFront-Viewer-Address` header (spoof-resistant) |
| Multi-session | Allowed; rate limit aggregates across all sessions per IP |
| On breach | 429 response with friendly message + IST reset time |
| Storage | MongoDB `rate_limits` collection, TTL auto-expire via `expires_at` ISODate field |

## 7.2 Session Management

| Attribute | Value |
|-----------|-------|
| Session ID | UUID v4, generated client-side |
| Transport | `X-Session-ID` request header |
| Storage | MongoDB `sessions` collection |
| Expiry | 30 minutes inactivity (TTL index on `last_active`) |
| On expiry | Fresh conversation; no context carryover |
| Concurrent sessions | Multiple per IP allowed |
| LangGraph checkpoint | Co-located in session document (`graph_state` field) |

## 7.3 Streaming

| Attribute | Value |
|-----------|-------|
| Protocol | Server-Sent Events (SSE) via Lambda Function URL |
| Routing | CloudFront routes `/api/*` to Lambda Function URL origin |
| Content type | `text/event-stream` |
| Event types | `agent_status`, `clarification`, `portal_card`, `search_meta`, `error`, `done` |
| Granularity | Structured events (not raw LLM tokens) |
| Timeout | No hard timeout (Lambda Function URL, not API GW) |

## 7.4 Observability

### Langfuse Cloud (LLM layer)
- Trace per session, span per agent node
- Per-span: latency (ms), input/output token count, Bedrock cost estimate
- Confidence: simple proxy (log-probabilities if available from Bedrock)
- Hallucination flag: set when URL Validator drops a URL (proxy metric)
- Clarification round count per session

### CloudWatch (Infrastructure layer)
- Lambda: duration, error rate, cold start count, memory utilization
- Custom metrics via structured log markers: rate limit breaches, search completions, URL validation failures
- Alarms: Lambda error rate > 1%, cold starts > 10/min

## 7.5 Security (v1)

| Control | Implementation |
|---------|----------------|
| Transport | HTTPS everywhere (CloudFront, Lambda Function URL) |
| DDoS protection | AWS Shield Standard (included with CloudFront) |
| Secrets | GitHub Actions secrets → Terraform variables → Lambda env vars at deploy time |
| IP privacy | SHA-256 hash in search_logs, raw IP only in sessions/rate_limits (TTL-expiring) |
| Input validation | Message length limit (2000 chars), session ID format validation, control character stripping |
| CORS | Restricted to CloudFront domain origin |
| Rate limiting | 10 searches/IP/day inline check |
| Prompt injection | System prompt hardening (restrict to property search domain) |

> **v2 additions:** AWS WAF (Core Rule Set) on CloudFront, custom rate-based WAF rules, user-based auth (Cognito).

## 7.6 Performance Targets (v1)

| Metric | Target |
|--------|--------|
| End-to-end latency (happy path) | < 8 seconds |
| First SSE event (agent_status) | < 1 second |
| Cold start (Lambda) | < 3 seconds |
| URL HEAD validation (per portal) | < 2 seconds (timeout, skip on timeout) |
| Clarification response | < 3 seconds |
