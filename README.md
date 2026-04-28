# ReAct Research Agent

A small Streamlit app that uses a LangChain ReAct agent with a Tavily web-search tool and a Groq-hosted model.

## Setup

1. Install the dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure `.env` contains the keys required by the app.

3. Run the app:

```bash
streamlit run app.py
```

## Notes

- The app supports the existing `.env` variable names in this workspace: `Tavily_API_KEY` and `Groq_API_KEY`.
- The agent uses `openai/gpt-oss-120b` through Groq.
