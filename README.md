# ReAct Research Agent

An intermediate-level agent project with clear separation of concerns. The FastAPI backend lives in `app/api/server.py`, the React frontend lives in `web/`, and core logic is organized into core, agent, tools, memory, services, schemas, and utils modules.

## Project Layout

```
react-agent/
│
├── app/
│   ├── core/
│   ├── agent/
│   ├── tools/
│   ├── memory/
│   ├── services/
│   ├── schemas/
│   ├── utils/
│   └── cli.py
│
├── tests/
├── .env
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure `.env` contains the keys required by the app.

3. Start the FastAPI backend:

```bash
uvicorn app.api.server:app --reload --port 8000
```

4. Start the React frontend:

```bash
cd web
npm install
npm run dev
```

## CLI Runner

```bash
python -m app.cli "What is the latest news about the global economy?"
```

## Tests

```bash
python -m unittest
```

## Notes

- The app supports `Tavily_API_KEY` and `Groq_API_KEY` in `.env`.
- The agent uses `openai/gpt-oss-120b` through Groq.
- Frontend expects the API at `http://localhost:8000` or `VITE_API_URL`.
