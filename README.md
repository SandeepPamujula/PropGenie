# PropGenie

[![CI Pipeline](https://github.com/SandeepPamujula/PropGenie/actions/workflows/ci.yml/badge.svg)](https://github.com/SandeepPamujula/PropGenie/actions/workflows/ci.yml)

AI-powered real estate search assistant for India.

## Project Structure
- `frontend/`: Next.js application (Static Export)
- `backend/`: Python LangGraph agents on AWS Lambda
- `infra/`: Terraform IaC
- `docs/`: HLD and Milestone documentation
- `prompts/`: Architecture and agent prompts

## Prerequisites
- Node.js 18+
- Python 3.12+
- AWS CLI configured
- MongoDB Atlas account

## Getting Started
### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

### Backend
1. `cd backend`
2. `python -m venv .venv`
3. `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
4. `pip install -r requirements.txt`
5. `python server.py`
