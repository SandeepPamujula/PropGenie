# 4. Component Inventory

| Component | Type | Technology | Responsibility |
|-----------|------|------------|----------------|
| Next.js Frontend | Static SPA | Next.js (static export) | Chat UI, SSE consumption, session ID generation |
| CloudFront CDN | CDN | AWS CloudFront | Serve static assets, extract CloudFront-Viewer-Address, route `/api/*` to Lambda Function URL |
| S3 Bucket | Object Store | AWS S3 | Host static frontend assets |
| PropGenie Agent | Lambda Function URL | Python 3.12 + LangGraph | Monolithic agent graph with all 5 agent nodes + inline rate limiting |
| MongoDB Atlas | Database | MongoDB 7.x | Sessions, rate limits, search logs, LangGraph checkpoints |
| AWS Bedrock | LLM Service | Llama 3.1 70B Instruct | NLU, entity extraction, location mapping, clarification |
| Langfuse Cloud | Observability | Langfuse SaaS | LLM tracing, span metrics, cost tracking |
| CloudWatch | Monitoring | AWS CloudWatch | Lambda metrics, alarms |
| GitHub Actions Secrets | Config | GitHub Actions | MongoDB URI, Langfuse keys → injected as Lambda env vars via Terraform |
| Terraform | IaC | Terraform + S3 backend | All AWS resources (dev + prod workspaces) |
| GitHub Actions | CI/CD | GitHub Actions | Lint, test, plan, apply, deploy pipelines |

---

## Agent Responsibility Matrix

| Responsibility | Orchestrator | Clarification | Query Builder | URL Validator | Formatter |
|----------------|:---:|:---:|:---:|:---:|:---:|
| Intent classification (buy/rent) | ✅ | | | | |
| Entity extraction | ✅ | | | | |
| Completeness check | ✅ | | | | |
| Clarification round tracking | ✅ | | | | |
| Route decision (clarify vs build) | ✅ | | | | |
| Generate clarifying question | | ✅ | | | |
| Enforce max 3 rounds | ✅ | | | | |
| Apply defaults (radius, budget) | | | ✅ | | |
| Map location to portal locality | | | ✅ | | |
| Build portal-specific URLs | | | ✅ | | |
| Structural schema validation | | | | ✅ | |
| HTTP HEAD liveness check | | | | ✅ | |
| Drop invalid URLs silently | | | | ✅ | |
| Format portal cards for SSE | | | | | ✅ |
| Add default/assumption notes | | | | | ✅ |

> **Note:** Rate limiting is handled inline in the Lambda handler (before the graph executes), not by any agent node.
