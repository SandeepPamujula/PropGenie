# PropGenie — High-Level Design Document

**Version:** 1.1  
**Date:** 2026-05-16  
**Status:** Draft  

---

## 1. Executive Summary

PropGenie is a conversational AI assistant that helps users in India find properties to buy or rent. Users interact through a chat interface — describing what they're looking for in natural language — and receive curated deep-link search URLs from two major Indian real estate portals: NoBroker and 99acres.

The system is built on a **multi-agent architecture** orchestrated by LangGraph, running as a single AWS Lambda function. Llama 3.1 70B Instruct (via AWS Bedrock) powers the natural language understanding. The frontend is a statically exported Next.js application hosted on S3 + CloudFront, styled after Perplexity's clean, modern interface. Real-time responses stream to the user via Server-Sent Events (SSE) through a Lambda Function URL, with CloudFront routing `/api/*` requests directly to the function.

MongoDB Atlas provides all persistence — session state, rate limits, search analytics, and LangGraph checkpoint storage. Langfuse Cloud provides LLM-specific observability, while AWS CloudWatch handles infrastructure monitoring. The entire stack is defined in Terraform (dev + prod workspaces) and deployed via GitHub Actions from a mono-repo.

---

## 2. Design Decisions Register

All decisions below were finalized during the architecture review:

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Lambda topology | Monolithic — single Lambda hosts entire LangGraph graph | Avoids inter-Lambda latency, simplifies cold starts, natural fit for LangGraph's single-process graph model |
| D2 | LangGraph state checkpoint | MongoDB `sessions` collection | Single data store strategy; avoids adding DynamoDB; session + graph state co-located |
| D3 | SSE streaming | CloudFront → Lambda Function URL (direct) | CloudFront routes `/api/*` to Lambda Function URL, which provides native response streaming without timeout limits. No API Gateway needed for v1 |
| D4 | Stream event format | Structured events only (`agent_status`, `portal_card`, `error`) | Cleaner UX than raw token streaming; aligns with Perplexity-style progressive rendering |
| D5 | Location resolution | LLM-based (v1) | Simplest to ship; geocoding API upgrade planned for v2 if free tier limits allow |
| D6 | Portal adapter config | Static YAML/JSON deployed with Lambda | No hot-reload needed for v1; portal schemas change infrequently |
| D7 | URL validation | Structural schema check + HTTP HEAD request | HEAD request catches dead/redirected URLs without downloading page content |
| D8 | Frontend architecture | Next.js static export, no BFF, direct API calls | Simplest deployment (S3 + CloudFront); no server-side rendering needed |
| D9 | UI style | Perplexity-inspired clean interface | Modern, card-based, conversational UX |
| D10 | IP extraction | CloudFront `CloudFront-Viewer-Address` header | More reliable than `X-Forwarded-For`; resistant to spoofing |
| D11 | Rate limit scope | 10 search flows per IP per calendar day (IST) | Clarification rounds don't count; only completed search invocations increment counter |
| D12 | Rate limit enforcement | Inline check in agent handler | Rate limit logic runs at the start of the Lambda handler, checking MongoDB before invoking the graph. No separate authorizer Lambda for v1 |
| D13 | MongoDB hosting | Atlas (user-supplied connection URL) | Managed service; no tier locked — user provisions |
| D14 | Search log retention | Indefinite | Analytics value; storage cost acceptable at projected volume |
| D15 | LLM provider | AWS Bedrock — Llama 3.1 70B Instruct (`us.meta.llama3-1-70b-instruct-v1:0`) | Strong instruction-following, cost-effective, available on Bedrock |
| D16 | LLM observability | Langfuse Cloud (SaaS) | Zero infra overhead for v1 |
| D17 | Confidence scoring | Simple proxy (token log-probabilities if available) | Self-consistency sampling deferred to v2 (cost) |
| D18 | Domain | Default CloudFront domain | No custom domain for v1 |
| D19 | Repo structure | Mono-repo | Single CI/CD pipeline; simpler for small team |
| D20 | Error UX | Graceful degradation message | User sees friendly message, not stack traces |
| D21 | Multi-session | Allowed; rate limit counts across all sessions per IP | UUID-based sessions; IP is the rate-limit key |
| D22 | Portal scope (v1) | NoBroker + 99acres only | Two portals cover buy and rent; remaining portals (MagicBricks, Housing.com, Square Yards) deferred to v2 |
| D23 | Security (v1) | CloudFront + inline validation | CloudFront provides HTTPS, DDoS protection (Shield Standard), and IP extraction. WAF deferred to v2 |
