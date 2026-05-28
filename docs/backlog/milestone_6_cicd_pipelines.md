# Milestone 6 — CI/CD Pipelines (GitHub Actions)

> **Goal:** Implement the three GitHub Actions workflows (feature CI, dev deploy, prod deploy) covering linting, testing, Terraform apply, Lambda packaging, frontend build/deploy, and smoke testing.

---

## US-6.1 — Feature Branch CI Pipeline

**User Story:**
As a **developer**,
I want automated linting, unit testing, and Terraform validation on every feature branch push,
So that code quality issues are caught before merging to main.

**Tasks:**
- Create `.github/workflows/ci.yml` triggered on `push` to `feature/*` and PRs to `main`
- Job 1 — Frontend: setup Node 20, `npm ci`, `npx eslint src/`, `npm test`
- Job 2 — Backend: setup Python 3.12, install deps, `ruff check backend/`, `pytest backend/tests/`
- Job 3 — Terraform: `terraform init -backend=false`, `terraform validate`, `terraform plan -var-file=environments/dev.tfvars`
- All 3 jobs run in parallel
- Add CI status badge to `README.md`

**Acceptance Criteria:**
- Pipeline triggers on pushes to `feature/*` and PRs to `main`
- All 3 jobs run concurrently; pipeline fails if any step fails
- Completes in under 5 minutes for a clean run
- README badge reflects current CI status

**Status:** Completed

---

## US-6.2 — Dev Deployment Pipeline

**User Story:**
As a **developer**,
I want automated deployment to dev on every merge to main,
So that the latest code is always live in dev for testing.

**Tasks:**
- Create `.github/workflows/deploy-dev.yml` triggered on `push` to `main`
- Step 1: Run lint + test checks
- Step 2: `terraform workspace select dev && terraform apply -auto-approve -var-file=environments/dev.tfvars` with secrets as `-var` args
- Step 3: Package Lambda — `pip install --platform manylinux2014_x86_64 --only-binary=:all: -t dist/`, zip, `aws lambda update-function-code` for Agent
- Step 4: `npm run build`, `aws s3 sync out/ s3://propgenie-frontend-dev/ --delete`, CloudFront invalidation
- Step 5: Smoke test — `curl -f https://<dev-domain>/api/health`, assert 200

**Acceptance Criteria:**
- Auto-triggers on merge to `main`
- Terraform, Lambda, and frontend all deploy successfully
- Smoke test confirms health endpoint returns 200
- All secrets from GitHub Actions secrets (never hardcoded)
- Completes in under 10 minutes

**Status:** Completed

---

## US-6.3 — Production Deployment Pipeline

**User Story:**
As a **DevOps engineer**,
I want a manually-triggered production deployment with approval gates,
So that production releases are deliberate and auditable.

**Tasks:**
- Create `.github/workflows/deploy-prod.yml` triggered on `workflow_dispatch`
- Same steps as dev pipeline but targeting prod workspace, prod Lambda, and prod S3/CloudFront
- Add GitHub environment protection rules (manual approval required for `prod`)
- Log deployment metadata: commit SHA, deployer, timestamp
- Document rollback procedure (re-deploy previous commit)

**Acceptance Criteria:**
- Only runs when manually triggered
- Requires approval before execution
- Smoke test confirms prod health endpoint returns 200
- Deployment metadata is logged

**Status:** Completed

---

## US-6.4 — Secrets & Environment Configuration

**User Story:**
As a **DevOps engineer**,
I want all credentials in GitHub Actions secrets flowing securely to Lambda env vars via Terraform,
So that no secrets are hardcoded or visible in logs.

**Tasks:**
- Configure 7 GitHub secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `MONGODB_URI`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`
- Create `dev` and `prod` GitHub environments; `prod` requires reviewer approval
- Document the secrets flow: GitHub Secrets → Terraform vars → Lambda env vars
- Create `.env.example` at repo root listing all required environment variables (no values)
- Verify secrets are masked in CI logs

**Acceptance Criteria:**
- All 7 secrets configured; `prod` environment has protection rules
- Terraform receives secrets via `-var` (not in tfvars)
- No secrets in CI logs
- `.env.example` documents all required environment variables
- README documents required secrets and setup procedure

**Status:** Completed
