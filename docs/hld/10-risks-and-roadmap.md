# 10. Risk & Mitigation

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| R1 | **Portal URL schema drift** — NoBroker or 99acres change their URL structure, breaking deep links | High | High | Static portal adapter configs (YAML) make updates a config-only change. HTTP HEAD validation catches broken URLs at runtime and drops them silently. Monitor `portals_dropped` in search_logs for early detection. Weekly automated portal validation job (GitHub Actions). |
| R2 | **LLM hallucination** — Llama 3.1 70B fabricates locality names or invalid URL parameters | High | Medium | URL Validator agent provides structural + liveness (HEAD) checks. Hallucination flag in Langfuse traces when URLs fail validation. Location mapping errors tracked as a dedicated metric. v2: switch to geocoding API. |
| R3 | **Lambda cold starts** — Python + LangGraph + dependencies = large package, slow cold starts | Medium | High | Keep Lambda package lean (exclude dev deps). Set provisioned concurrency for prod (5 instances). Monitor cold start count in CloudWatch; alarm at >10/min. v2: consider container image Lambda or EKS. |
| R4 | **IP spoofing / rate limit bypass** — Attackers attempt to circumvent IP-based rate limits | Medium | Medium | Use CloudFront `CloudFront-Viewer-Address` header (set by CloudFront, not client-controllable). v2: add WAF managed rules and migrate to user-based rate limiting with Cognito auth. |
| R5 | **MongoDB Atlas connectivity** — Lambda may have connectivity issues to Atlas over public internet | Medium | Low | Connection pooling via `pymongo` with appropriate `maxPoolSize`. Retry logic with exponential backoff. CloudWatch alarm on connection errors. v2: Atlas peering or PrivateLink. |
| R6 | **Bedrock throttling** — High concurrent usage may hit Bedrock provisioned throughput limits for Llama 3.1 70B | Medium | Low | Request Bedrock quota increase for production. Implement graceful degradation: return friendly error message. Monitor Bedrock throttle events. |
| R7 | **SSE connection drops** — Network interruptions break the event stream mid-response | Low | Medium | Frontend implements reconnection logic with `X-Session-ID` to resume. Last event ID tracking. If reconnection fails, show "connection lost" with retry button. |
| R8 | **Cost overrun** — Unexpected traffic spike causes high Bedrock/Lambda costs | Medium | Low | CloudWatch billing alarms. Lambda concurrency limit as a hard cap. v2: WAF rate-based rules as additional throttling. |
| R9 | **Lambda Function URL exposure** — Public Lambda Function URL accessible without WAF | Low | Low | CloudFront is the intended entry point. Mitigated in v1 by restricting Lambda Function URL via AWS_IAM auth + CloudFront OAC for Lambda origins. |

---

# 11. V2 Roadmap (Out of Scope for v1)

| Priority | Feature | Rationale |
|----------|---------|-----------|
| P1 | **Additional portals (MagicBricks, Housing.com, Square Yards)** | Expand portal coverage beyond NoBroker and 99acres. Requires researching URL schemas for each portal. |
| P2 | **AWS WAF on CloudFront** | Add Core Rule Set (SQLi, XSS, bot detection) and custom rate-based rules for defense-in-depth. |
| P3 | **Geocoding API for location resolution** | Replace LLM-based location mapping with Google Maps / Nominatim API for accurate lat/lng → portal locality mapping. Reduces hallucination risk significantly. |
| P4 | **User authentication (Cognito)** | Enables user-based rate limiting (replacing IP-based), preference persistence, and search history across sessions. |
| P5 | **Hindi + regional language support** | Bedrock translation layer before Orchestrator. Expand addressable user base across India. |
| P6 | **Portal API integrations** | If portals offer partner APIs, fetch live listing counts alongside deep links. Richer user experience. |
| P7 | **Custom domain** | `propgenie.in` for frontend, `api.propgenie.in` for API. ACM certificate + Route53. |
| P8 | **EKS migration** | If Lambda concurrency limits are hit, migrate LangGraph workload to EKS for horizontal scaling. |
| P9 | **Personalization** | Remember user preferences across sessions (requires auth). Suggest searches based on history. |
| P10 | **Map view** | Embed geo-search UI (Mapbox/Google Maps) alongside portal links. Show property clusters on map. |
| P11 | **Advanced filters** | Furnishing level, floor preference, property age, amenities. |
| P12 | **Self-consistency confidence scoring** | Multiple LLM calls to estimate confidence. Expensive but more accurate than log-prob proxy. |
