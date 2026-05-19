# Milestone 3 — AWS Infrastructure (Terraform)

> **Goal:** Provision the complete AWS infrastructure using Terraform modules — Lambda function with Function URL, CloudFront distribution + S3, and CloudWatch monitoring. Dev and prod workspaces with environment-specific configurations.

---

## US-13 — Lambda Function Module

**User Story:**
As a **DevOps engineer**,
I want the PropGenie Agent deployed as a Lambda function with a least-privilege IAM role,
So that the backend runtime is provisioned securely and supports SSE streaming via Function URL.

**Tasks:**
- Create `infra/modules/lambda/main.tf`:
  - PropGenie Agent Lambda (Python 3.12 runtime, Function URL enabled for SSE streaming)
  - IAM execution role with least-privilege policies: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `logs:CreateLogStream`, `logs:PutLogEvents`
  - Environment variables: `MONGODB_URI`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`, `ENVIRONMENT`
- Create `infra/modules/lambda/variables.tf` with inputs: `environment`, `lambda_memory`, `lambda_timeout`, `mongodb_uri`, `langfuse_*`
- Create `infra/modules/lambda/outputs.tf` exporting: `agent_function_url`, `agent_function_arn`
- Configure Lambda Function URL with `AWS_IAM` auth type and grant `lambda:InvokeFunctionUrl` to CloudFront OAC
- Set reserved concurrency appropriately (dev: 5, prod: 20)

**Acceptance Criteria:**
- `terraform plan` shows the Lambda function with correct runtime, memory, and timeout
- IAM policies follow least-privilege (Bedrock invoke for Llama 3.1 70B model ARN + CloudWatch logs)
- Lambda Function URL is created for the Agent function
- Environment variables are set correctly from Terraform variables

**Status:** Completed

---

## US-14 — Frontend Hosting Module (S3 + CloudFront)

**User Story:**
As a **DevOps engineer**,
I want the Next.js static export served via S3 and CloudFront with `/api/*` routing to the Lambda Function URL,
So that the frontend is globally distributed and API requests are proxied through the same domain.

**Tasks:**
- Create `infra/modules/frontend/main.tf`:
  - S3 bucket for static assets (block public access, enable versioning)
  - CloudFront Origin Access Control (OAC) for S3 and Lambda Function URL
  - CloudFront distribution:
    - S3 origin for static assets (default behavior)
    - Lambda Function URL origin for `/api/*` requests (ordered behavior)
    - `CloudFront-Viewer-Address` header forwarded via origin request policy for `/api/*`
    - Default root object: `index.html`
    - Custom error response: 403/404 → `index.html` (SPA routing)
- Create `infra/modules/frontend/variables.tf` with inputs: `environment`, `agent_function_url`, `price_class`
- Create `infra/modules/frontend/outputs.tf` exporting: `cloudfront_domain`, `s3_bucket_name`, `distribution_id`

**Acceptance Criteria:**
- CloudFront distribution serves static content from S3 and proxies `/api/*` to the Lambda Function URL
- `CloudFront-Viewer-Address` header is forwarded to the Lambda origin (used for rate limiting in the handler)
- SPA routing works (direct URL access to any path serves `index.html`)

**Status:** Completed

---

## US-15 — CloudWatch Monitoring Module

**User Story:**
As a **DevOps engineer**,
I want CloudWatch log groups, metric filters, and alarms configured for the Lambda function,
So that operational issues are detected and alerted on promptly.

**Tasks:**
- Create `infra/modules/monitoring/main.tf`:
  - Log group for Agent Lambda (retention: dev 7 days, prod 30 days)
  - Metric filters:
    - Lambda error count (filter pattern: `ERROR`)
    - Rate limit breach count (filter pattern: `RATE_LIMIT_EXCEEDED`)
    - Cold start count (filter pattern: `Init Duration`)
  - CloudWatch alarms:
    - Lambda error rate > 1%
    - Cold starts > 10 per minute
  - SNS topic for alarm notifications
- Create `infra/modules/monitoring/variables.tf` with inputs: `environment`, `agent_function_name`, `alarm_email`
- Create `infra/modules/monitoring/outputs.tf` exporting: `alarm_topic_arn`

**Acceptance Criteria:**
- Log groups are created with correct retention
- Metric filters parse Lambda logs
- Alarms trigger on defined thresholds

**Status:** Not Started

---

## US-16 — Terraform Root Module Composition

**User Story:**
As a **DevOps engineer**,
I want the root Terraform configuration to compose all modules together with proper input/output wiring,
So that a single `terraform apply` provisions the entire stack.

**Tasks:**
- Wire `infra/main.tf` to invoke all modules: `lambda`, `frontend`, `monitoring`
- Pass outputs between modules (e.g., `lambda.agent_function_url` -> `frontend.agent_function_url`)
- Configure environment-specific values in `dev.tfvars` and `prod.tfvars`
- Define sensitive variables supplied via CI/CD secrets: `mongodb_uri`, `langfuse_secret_key`, etc.
- Populate `infra/outputs.tf` with CloudFront domain

**Acceptance Criteria:**
- `terraform plan` succeeds for dev and prod
- All module outputs are properly wired

**Status:** Not Started
