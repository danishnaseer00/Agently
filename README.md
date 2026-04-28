# ReAct Research Agent

An intermediate-level agent project with clear separation of concerns. The Streamlit UI lives in `app/main.py`, while core logic is organized into core, agent, tools, memory, services, schemas, and utils modules.

## Project Layout

```
react-agent/
│
├── app/
│   ├── main.py
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

3. Run the Streamlit UI (recommended):

```bash
streamlit run app.py
```

If you prefer running the module directly:

```bash
streamlit run app/main.py
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
