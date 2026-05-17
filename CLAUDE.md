# PropGenie Agent Guidelines (CLAUDE.md)

This file contains commands and rules for development in the PropGenie mono-repo.

## Development Commands

### Frontend (Next.js)
* **Install dependencies:** `cd frontend && npm install`
* **Run development server:** `cd frontend && npm run dev`
* **Build / Export static site:** `cd frontend && npm run build`
* **Linting:** `cd frontend && npm run lint`

### Backend (Python 3.12 / FastAPI / LangGraph)
* **Setup virtual environment:** `cd backend && python -m venv .venv && source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
* **Install dependencies:** `cd backend && pip install -r requirements.txt`
* **Run local FastAPI server:** `cd backend && uvicorn server:app --reload --port 8000`
* **Run tests:** `cd backend && pytest`

---

## Agent & Backlog Management Rules

### 1. Milestone Tracking & Status Updates (CRITICAL)
Whenever you start working on a User Story or complete it, you **MUST** update its status in the corresponding milestone documentation file under `docs/backlog/`:
* **In Progress:** When you begin implementation of a User Story, change its status in the markdown file to `**Status:** In Progress`.
* **Completed:** When a User Story is fully implemented and meets all acceptance criteria, change its status to `**Status:** Completed`.
* Keep the milestone files updated as the single source of truth for project progress.

### 2. Code Quality & Standards
* **Backend:** Maintain strict type hints in Python using `Pydantic` and `TypedDict` for LangGraph state. All database interactions should go through `backend/db/`.
* **Frontend:** Use Next.js Static Export conventions. Avoid using the Next.js `app/api` directory to prevent routing conflicts with the backend.
* **Observability:** Instrument all agent nodes with Langfuse tracing spans.
