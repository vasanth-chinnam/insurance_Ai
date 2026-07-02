# InsureAI — Agentic Insurance Automation Suite

InsureAI is a state-of-the-art insurance automation system powered by multi-agent orchestration, Retrieval-Augmented Generation (RAG), computer vision, and weather index monitoring. It automates claims processing, fraud detection, risk profiling, policy comparison, and notifications across multiple insurance domains (Motor, Health, Travel, and Crop).

## Architecture Overview

```mermaid
graph TD
    User([User Chat/Dashboard]) --> Orchestrator[Orchestrator Agent]
    Orchestrator --> Classifier[Intent Classifier]
    Orchestrator --> PolicyRAG[Policy RAG Agent]
    Orchestrator --> Claims[Motor Claims Agent]
    Orchestrator --> Fraud[Fraud Detector]
    Orchestrator --> Risk[Risk Profiler]
    Orchestrator --> Renewal[Renewal Agent]
    Orchestrator --> Crop[Crop Payout Agent]
    
    Claims --> DB[(SQLite / Supabase)]
    Fraud --> DB
    Risk --> DB
    Renewal --> DB
    
    Orchestrator --> SMS[Twilio Notification Service]
```

---

## Feature Matrix

| Phase | Component | Key Features | Status |
|---|---|---|---|
| **Phase 1** | **Policy RAG** | Chat with policy docs using Qdrant vector database, chunking & semantic search. | Completed |
| **Phase 2** | **Motor Claims** | Vision damage analysis with cost breakdowns, deductibles & automatic DB logging. | Completed |
| **Phase 3** | **Fraud Detection** | AI heuristics & claims history comparison to calculate risk scores & flag claims. | Completed |
| **Phase 4** | **Risk Profiler** | Domain rules assessment for health/lifestyle to suggest premium adjustments. | Completed |
| **Phase 5** | **Crop Agent** | Weather data monitoring (rainfall & temperature) to trigger crop yield loss payouts. | Completed |
| **Phase 6** | **Renewal Agent** | Policy renewal negotiation, switching analysis, and competitor premium savings. | Completed |
| **Phase 7** | **Integration / SMS** | Full claim pipeline chaining, database automation, and Twilio SMS notification service. | Completed |
| **Week 1** | **SaaS Foundation** | Multi-tenant database schema, JWT auth tokens containing `tenant_id`/`role`, and tenant isolation middleware. | Completed |

---

## Quick Start

### 1. Local Run (Manual)
1. **Qdrant**: Ensure a local Qdrant server is running:
   ```bash
   docker run -d -p 6333:6333 qdrant/qdrant
   ```
2. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
3. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### 2. Containerized Run (Docker Compose)
Run the entire suite (Frontend + Backend + Qdrant) with one command:
```bash
docker compose up -d --build
```
Verify containers are running:
```bash
docker compose ps
```

---

## API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Conversational interface with RAG fallback. |
| `POST` | `/upload` | PDF/TXT policy ingestion. |
| `POST` | `/claims/motor` | File motor claim (requires damage photo). |
| `POST` | `/fraud/analyze` | Run fraud risk assessment. |
| `POST` | `/risk/profile` | Calculate risk score and category. |
| `POST` | `/renewal/negotiate` | Negotiate renewal comparing current policy. |
| `POST` | `/crop/analyze` | Weather data payout validation. |
| `POST` | `/automation/run` | Multi-agent execution orchestrator. |

---

## Environment Variables Reference

Create a `.env` file in the project root:

```ini
# Gemini API Key (Required for RAG, vision, and orchestration)
GOOGLE_API_KEY=AIzaSy...

# Qdrant Database URL
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=insurance_policies

# Twilio SMS Notifications (Optional)
TWILIO_SID=AC...
TWILIO_TOKEN=token...
TWILIO_FROM=+1...

# PostgreSQL production database (Optional)
DATABASE_URL=postgresql://user:pass@host:port/db
```

---

## Cloud Deployment Guide

### Frontend (Vercel)
1. Install Vercel CLI: `npm install -g vercel`
2. Run `vercel` in `frontend/` directory.
3. Configure Environment Variables pointing to your backend endpoint (e.g. `VITE_API_BASE_URL`).

### Backend (Render)
1. Create a Web Service on Render connected to your repository.
2. Select Python environment.
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Configure environmental variables.

### Database (Supabase PostgreSQL migration)
Update `backend/db.py` to use `psycopg2` using the `DATABASE_URL` connection string:
```python
import os
import psycopg2

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))
```
Ensure tables are initialized on startup using `init_db()`.

---

## SaaS Week 1: Multi-Tenant Foundation

The platform is transformed into a multi-tenant B2B SaaS system:
- **Tenant Middleware**: Resolves the tenant context for each request using headers (e.g., `X-Tenant-ID`) or defaults.
- **Tenant-Aware Queries**: Automatic tenant scoping applied to SQL queries using the new `tenant_query` helper.
- **JWT Authentication**: Secure tokens containing `sub`, `email`, `role`, and `tenant_id` claims to enforce data isolation at the API layer.

