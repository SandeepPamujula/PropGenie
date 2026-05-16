# Milestone 1 — Project Foundation & Dev Environment

> **Goal:** Establish the mono-repo structure, local development tooling, and Terraform state backend so that all subsequent milestones have a stable foundation.

---

## US-01 — Mono-Repo Scaffolding

**User Story:**
As a **developer**,
I want a well-organized mono-repo with clearly separated frontend, backend, infra, and CI/CD directories,
So that I can navigate the codebase efficiently and each team can work independently.

**Tasks:**
- Create the top-level directory structure: `frontend/`, `backend/`, `infra/`, `docs/`, `prompts/`, `.github/workflows/`
- Initialize `frontend/` with a Next.js project configured for static export (`output: 'export'` in `next.config.js`)
- Initialize `backend/` with Python 3.12 project structure:
  - `agents/` — agent node implementations
  - `models/` — Pydantic schemas and TypedDicts
  - `db/` — MongoDB connection and data access
  - `utils/` — shared utilities (config loader, rate limiter, logger)
  - `observability/` — Langfuse tracing
  - `portal_configs/` — static YAML portal adapters
  - `tests/` with `unit/`, `integration/`, `performance/` subdirectories
- Create stub files for all 5 agents: `orchestrator.py`, `clarification.py`, `query_builder.py`, `url_validator.py`, `response_formatter.py`
- Create `backend/graph.py` (LangGraph graph definition stub)
- Create `backend/handler.py` (Lambda handler entry point stub)
- Create `backend/server.py` (FastAPI local dev server with CORS enabled for `http://localhost:3000`)
- Create `.env.example` with all required environment variables (no values)
- Add `.gitignore` for Python (`__pycache__`, `.venv`, `dist/`, `.env`) and Node (`node_modules/`, `.next/`, `out/`)
- Create a root `README.md` with project overview, prerequisites, and quick-start instructions

**Acceptance Criteria:**
- Running `ls` at the repo root shows: `frontend/`, `backend/`, `infra/`, `docs/`, `prompts/`, `.github/`, `README.md`, `.env.example`
- `cd frontend && npm install && npm run build` succeeds and produces a `out/` directory
- `cd backend && python -c "import agents.orchestrator"` succeeds without error
- `.gitignore` prevents `node_modules/`, `__pycache__/`, `.venv/`, `out/`, and `.env` from being committed
- `backend/server.py` starts with `uvicorn server:app --reload --port 8000` and returns 200 on `/api/health`

**Status:** Not Started

---

## US-02 — Python Backend Dev Environment

**User Story:**
As a **backend developer**,
I want a reproducible Python development environment with linting, formatting, and test tooling pre-configured,
So that I can write consistent, high-quality code from day one.

**Tasks:**
- Create `backend/requirements.txt` with pinned production dependencies: `langgraph`, `langchain-aws`, `boto3`, `pymongo`, `langfuse`, `pydantic`, `fastapi`, `uvicorn`
- Create `backend/requirements-dev.txt` with dev dependencies: `pytest`, `pytest-asyncio`, `ruff`, `mypy`, `moto`, `httpx`
- Create `backend/pyproject.toml` with Ruff configuration (line length 120, Python 3.12 target)
- Create `backend/tests/conftest.py` with shared fixtures (mock MongoDB client, mock Bedrock client)
- Add a Makefile or `scripts/` entry for common commands: `lint`, `format`, `test`, `typecheck`

**Acceptance Criteria:**
- `cd backend && pip install -r requirements.txt -r requirements-dev.txt` completes without errors
- `ruff check backend/` produces zero findings on the initial scaffold
- `pytest tests/` runs and passes (at least one placeholder test)
- `mypy backend/ --ignore-missing-imports` returns no errors

**Status:** Not Started

---

## US-03 — Frontend Dev Environment

**User Story:**
As a **frontend developer**,
I want the Next.js project configured with ESLint, TypeScript, and a base UI layout,
So that I can begin building the chat interface with proper tooling.

**Tasks:**
- Configure `frontend/tsconfig.json` for strict TypeScript
- Configure ESLint with Next.js recommended rules
- Create `frontend/src/app/layout.tsx` with base HTML structure and meta tags
- Create `frontend/src/app/page.tsx` with a placeholder chat UI shell (empty conversation area + input field)
- Add Google Font import (Inter or Outfit) to layout
- Create `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000` for local development
- Verify static export works: `npm run build` outputs to `out/`

**Acceptance Criteria:**
- `cd frontend && npx eslint src/` produces zero errors
- `npm run build` succeeds and generates a valid `out/index.html`
- Opening `out/index.html` in a browser shows the placeholder chat shell
- TypeScript strict mode is enabled and no type errors exist
- `NEXT_PUBLIC_API_URL` is configurable via environment variable

**Status:** Not Started

---

## US-04 — Terraform State Backend

**User Story:**
As a **DevOps engineer**,
I want a Terraform S3 backend with DynamoDB state locking provisioned,
So that infrastructure state is stored securely and concurrent applies are safe.

**Tasks:**
- Create `infra/backend-setup/main.tf` to bootstrap the state backend (one-time manual apply):
  - S3 bucket `propgenie-terraform-state` with versioning enabled
  - DynamoDB table `propgenie-terraform-lock` with `LockID` partition key
  - Bucket policy restricting access to the deploying IAM principal
- Create `infra/main.tf` with provider configuration (AWS, `ap-south-1`) and S3 backend block
- Create `infra/variables.tf` with core variables: `environment`, `project_name`, `aws_region`
- Create `infra/environments/dev.tfvars` and `infra/environments/prod.tfvars` with environment-specific values
- Create `infra/outputs.tf` as a placeholder

**Acceptance Criteria:**
- `cd infra/backend-setup && terraform init && terraform plan` shows the S3 bucket and DynamoDB table resources
- After bootstrap apply, `cd infra && terraform init` successfully configures the S3 backend
- `terraform workspace new dev && terraform workspace new prod` both succeed
- State file is stored in `s3://propgenie-terraform-state/<workspace>/terraform.tfstate`

**Status:** Not Started

---

## US-05 — Portal Adapter Configuration

**User Story:**
As a **backend developer**,
I want static YAML configuration files for each real estate portal's URL schema,
So that the Query Builder Agent can construct deep-link URLs without hardcoded logic and new portals can be added via config alone.

**Tasks:**
- Research NoBroker and 99acres URL structures for buy and rent flows across multiple cities
- Create `backend/portal_configs/nobroker.yaml` with base URL, parameter mappings, city slug map, and example URLs for buy and rent
- Create `backend/portal_configs/99acres.yaml` with the same structure
- Define a shared Pydantic schema for portal config validation (`backend/models/portal_config.py`)
- Write a config loader utility that reads all YAML files and validates against the schema (`backend/utils/config_loader.py`)
- Write unit tests for the config loader

**Acceptance Criteria:**
- Both YAML files parse without error and pass Pydantic validation
- Config loader returns a `dict[str, PortalConfig]` keyed by `portal_id`
- Each config contains at minimum: `portal_id`, `base_url`, `params` mapping, `city_slug_map` for at least 5 Indian cities
- Adding a new portal requires only a new YAML file — no code changes
- Sample URLs generated from the config match real portal URL patterns

**Status:** Not Started
