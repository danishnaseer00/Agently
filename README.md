---
title: Agently
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Agently

An AI-powered research agent with **RAG (Retrieval-Augmented Generation)**, **vision analysis**, **tool calling**, and **web search** capabilities. Built with a FastAPI backend and React frontend.

## Features

- **🧠 Multi-Model AI Chat** — Powered by Groq (`openai/gpt-oss-120b`) with support for deep thinking, tool usage, and multi-turn conversations
- **📄 RAG (Retrieval-Augmented Generation)** — Upload PDFs, DOCX files, and documents. Content is chunked, embedded, and stored in Qdrant vector database for intelligent retrieval
- **🔍 Hybrid Search** — Combines semantic search (sentence-transformers) with keyword search (BM25) for accurate document retrieval, plus cross-encoder reranking
- **🌐 Web Search & Scraping** — Real-time web search via Tavily API with content scraping capabilities
- **👁️ Vision Analysis** — Image analysis and OCR powered by Groq's vision model
- **🛠️ Tool Calling** — ReAct agent with tools for file operations, web scraping, image analysis, and more
- **🔐 Authentication** — Clerk-powered auth (Google, GitHub, email sign-in)
- **💾 Persistent Memory** — Conversations stored in Supabase (PostgreSQL) with short-term context management
- **🎨 Modern UI** — Clean React frontend with tool panels, file uploads, and responsive design
- **/ Slash Commands** - Summarize for the summarizing the conversation and deepthink for thinking and research..
## Architecture

```
User → Frontend (React/Vite) → Backend (FastAPI/Docker) → Services
                                                              ├── Groq       (LLM + Vision)
                                                              ├── Qdrant     (Vector Database)
                                                              ├── Supabase   (PostgreSQL)
                                                              ├── Tavily     (Web Search)
                                                              └── Clerk      (Authentication)
```

## Services & Tools

| Service | Role |
|---|---|
| **Groq** | LLM inference and vision analysis — runs `openai/gpt-oss-120b` for chat and `llama-4-scout-17b` for vision |
| **Qdrant** | Vector database for RAG — stores document embeddings for semantic search |
| **Supabase** | PostgreSQL database for conversation history and user data |
| **Clerk** | Authentication provider — supports Google, GitHub, and email sign-in |
| **Tavily** | Web search API for real-time internet queries |
| **Sentence-Transformers** | Local embedding model (`all-MiniLM-L6-v2`) for document chunking |
| **LangChain** | Agent orchestration and tool execution framework |
| **FastAPI** | Backend API server with async support |
| **React + Vite** | Frontend framework with HMR and optimized builds |

## Project Layout

```
Agently/
│
├── app/
│   ├── api/
│   │   ├── middleware/     # CORS, logging
│   │   ├── routes/         # Health, chat, documents, images, tools endpoints
│   │   └── server.py       # FastAPI entry point
│   ├── core/               # Config, LLM setup (Groq integration)
│   ├── agent/              # ReAct agent: planner, parser, executor
│   ├── tools/              # File tool, search, web scraper, image tool
│   ├── memory/             # Conversation memory (short-term + Supabase)
│   ├── services/
│   │   ├── rag/            # Hybrid search, vector DB, reranking, config
│   │   └── vision/         # Image analysis, OCR pipeline
│   ├── schemas/
│   └── utils/              # Helpers, logging
│
├── web/                    # React frontend (Vite)
├── tests/                  # Smoke tests
├── Dockerfile              # Production Docker build
├── .env                    # Environment variables
├── requirements.txt
└── README.md
```

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- A `.env` file in the root with the required keys

### 1. Backend

```bash
pip install -r requirements.txt
uvicorn app.api.server:app --reload --port 8000
```

### 2. Frontend

```bash
cd web
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### 3. Run Tests

```bash
python -m unittest
```

## Environment Variables

### Backend (`app/.env` or root `.env`)

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key ([console.groq.com/keys](https://console.groq.com/keys)) |
| `TAVILY_API_KEY` | ✅ | Tavily search API key ([app.tavily.com](https://app.tavily.com)) |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon/public key |
| `CLERK_JWKS_URL` | ✅ | Clerk JWKS endpoint |
| `CLERK_SECRET_KEY` | ✅ | Clerk secret key |
| `MODEL_NAME` | Optional | Groq model override (default: `llama-3.3-70b-versatile`) |
| `CORS_ORIGINS` | Optional | Comma-separated frontend URLs for CORS |
| `QDRANT_MODE` | Optional | `memory` (local/test) or `remote` (production) |
| `QDRANT_URL` | For remote | Qdrant cluster URL |
| `QDRANT_API_KEY` | For remote | Qdrant API key |

### Frontend (`web/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ | Backend URL (`http://localhost:8000` for local dev) |
| `VITE_CLERK_PUBLISHABLE_KEY` | ✅ | Clerk publishable key |
