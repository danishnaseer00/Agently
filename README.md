---
title: Agently
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Agently

An AI-powered research agent with RAG (Retrieval-Augmented Generation), vision analysis, tool calling, and web search capabilities. Built with FastAPI backend + React frontend.

## Architecture

```
User → Vercel (Frontend) → Hugging Face Spaces Docker (Backend) → Supabase + Qdrant + Groq + Tavily + Clerk
```

| Layer | Tech | Hosting |
|---|---|---|
| **Frontend** | React + Vite | Vercel (free) |
| **Backend** | FastAPI (Python) | Hugging Face Spaces Docker (free) |
| **Database** | Supabase (PostgreSQL) + Qdrant (Vector DB) | Supabase free + Qdrant Cloud free |
| **Auth** | Clerk | Clerk free tier |
| **LLM** | Groq (`openai/gpt-oss-120b`) | Groq free tier |
| **Search** | Tavily | Tavily free tier |

> **Cold start:** Backend sleeps after 48h of inactivity (~30s wake). See [DEPLOYMENT.md](./DEPLOYMENT.md) for details.

---

## Project Layout

```
Agently/
│
├── app/
│   ├── api/
│   │   ├── middleware/     # CORS, logging
│   │   ├── routes/         # API endpoints
│   │   └── server.py       # FastAPI entry point
│   ├── core/               # Config, LLM setup
│   ├── agent/              # ReAct agent logic
│   ├── tools/              # File, search, web scraping tools
│   ├── memory/             # Conversation memory
│   ├── services/
│   │   ├── rag/            # Vector search, reranking
│   │   └── vision/         # Image analysis, OCR
│   ├── schemas/
│   └── utils/
│
├── web/                    # React frontend
├── tests/
│
├── Dockerfile              # Production Docker build
├── .dockerignore
├── .github/workflows/      # CI/CD — auto-deploy on push to main
├── web/vercel.json         # Vercel SPA routing
│
├── .env                    # Local environment variables
├── requirements.txt
└── README.md
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- A `.env` file in the root with the required keys (see below)

### 1. Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.api.server:app --reload --port 8000
```

### 2. Frontend

```bash
cd web
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API calls to `http://localhost:8000`.


### 3. Run Tests

```bash
python -m unittest
```

---

## Environment Variables

### Backend (`.env` file at project root)

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key (console.groq.com/keys) |
| `TAVILY_API_KEY` | ✅ | Tavily search API key (app.tavily.com) |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon/public key |
| `CLERK_JWKS_URL` | ✅ | Clerk JWKS endpoint |
| `CLERK_SECRET_KEY` | ✅ | Clerk secret key |
| `MODEL_NAME` | Optional | Groq model (default: `llama-3.3-70b-versatile`, set to `openai/gpt-oss-120b`) |
| `CORS_ORIGINS` | Optional | Comma-separated frontend URLs for CORS (e.g. `https://my-app.vercel.app`) |
| `QDRANT_MODE` | Optional | `memory` (local) or `remote` (cloud) |
| `QDRANT_URL` | For remote | Qdrant cluster URL |
| `QDRANT_API_KEY` | For remote | Qdrant API key |

### Frontend (`web/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ | Backend URL (`http://localhost:8000` for dev) |
| `VITE_CLERK_PUBLISHABLE_KEY` | ✅ | Clerk publishable key |

---

## Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for the complete step-by-step guide to deploy to **Vercel + Hugging Face Spaces** on **free tiers** (includes Docker setup, CI/CD, env vars, and troubleshooting).

### Deployment files created

| File | Purpose |
|---|---|
| `Dockerfile` | Multi-stage build with pre-downloaded ML models |
| `.dockerignore` | Excludes dev files from Docker build context |
| `.github/workflows/deploy.yml` | Auto-deploy backend to HF Spaces + frontend to Vercel |
| `web/vercel.json` | SPA routing for Vercel |
| `DEPLOYMENT.md` | Full deployment guide |

---

## Notes

- The agent uses `openai/gpt-oss-120b` through **Groq** (not OpenAI directly)
- Supports RAG (PDF, DOCX), web search, image analysis, and OCR
- Frontend uses Clerk for authentication
- CORS is configured to allow localhost (5173-5175) + any origins set in `CORS_ORIGINS`
