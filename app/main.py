from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agent.agent import build_agent
from app.core.config import load_settings
from app.core.llm import build_llm
from app.services.research_service import run_research
from app.tools.search import build_web_search_tool
from app.utils.helpers import trace_to_text

APP_TITLE = "ReAct Research Agent"
APP_SUBTITLE = (
    "An Agent that reasons step by step and uses web search "
    "whenever the answer may depend on recent or current information."
)


def ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_trace" not in st.session_state:
        st.session_state.last_trace = []


def render_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
            --bg: #f4efe7;
            --bg-2: #edf2ef;
            --surface: rgba(255, 255, 255, 0.78);
            --surface-strong: #ffffff;
            --text: #111827;
            --muted: #5b6472;
            --line: rgba(17, 24, 39, 0.08);
            --accent: #0f766e;
            --accent-2: #1d4ed8;
            --shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
        }

        .stApp {
            background:
                radial-gradient(circle at 15% 20%, rgba(15, 118, 110, 0.12), transparent 26%),
                radial-gradient(circle at 88% 12%, rgba(29, 78, 216, 0.10), transparent 24%),
                linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 100%);
            color: var(--text);
            font-family: 'Manrope', sans-serif;
        }

        html, body, [class*='css'] {
            font-family: 'Manrope', sans-serif;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            max-width: 1040px;
        }

        .hero {
            border: 1px solid var(--line);
            border-radius: 30px;
            padding: 1.35rem 1.5rem 1.25rem;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.84), rgba(255, 255, 255, 0.64));
            backdrop-filter: blur(12px);
            box-shadow: var(--shadow);
            margin-top: 0.5rem;
            margin-bottom: 0.85rem;
        }

        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            color: var(--accent);
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .hero h1 {
            margin: 0;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2.4rem;
            line-height: 1.05;
            letter-spacing: -0.05em;
            color: var(--text);
        }

        .hero p {
            margin: 0.65rem 0 0;
            color: var(--muted);
            font-size: 1.02rem;
            max-width: 70ch;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin: 0.3rem 0 0.9rem;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.45rem 0.8rem;
            background: rgba(255, 255, 255, 0.62);
            color: var(--muted);
            font-size: 0.84rem;
            font-weight: 700;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        }

        .card-title {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin: 0.15rem 0 0.45rem;
        }

        .trace-box {
            background: #fbfcfe;
            border: 1px solid #d9e2ec;
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-top: 0.5rem;
            color: #334155;
            font-size: 0.92rem;
            white-space: pre-wrap;
        }

        .stChatMessage[data-testid="stChatMessage"] {
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.84);
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
            border-radius: 18px;
            padding: 0.2rem 0.3rem;
        }

        .stChatMessage [data-testid="stMarkdownContainer"] p {
            font-size: 1rem;
            line-height: 1.7;
        }

        div[data-testid="stSidebar"] {
            display: none;
        }

        div[data-testid="stChatInput"] {
            border-top: 1px solid rgba(17, 24, 39, 0.06);
            padding-top: 0.8rem;
        }

        div[data-testid="stChatInput"] textarea {
            font-family: 'Manrope', sans-serif;
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.74);
            color: var(--text);
            font-weight: 700;
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(15, 118, 110, 0.3);
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
        }

        .stExpander {
            border-radius: 18px;
            border-color: var(--line);
            background: rgba(255, 255, 255, 0.5);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_agent_executor(temperature: float, max_results: int):
    settings = load_settings()
    tools = [build_web_search_tool(settings, max_results)]
    llm = build_llm(settings, temperature, tools)
    return build_agent(llm, tools)


def submit_prompt(prompt: str, agent_executor) -> None:
    if not prompt.strip():
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        with st.spinner("Researching the latest information..."):
            answer, trace = run_research(
                agent_executor,
                prompt,
                st.session_state.messages,
            )
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_trace = trace
    except Exception as exc:  # noqa: BLE001
        error_message = f"I could not complete the request: {exc}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        st.session_state.last_trace = []


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="search",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    ensure_state()
    render_css()

    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">LangChain ReAct Agent</div>
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="chip-row">
            <div class="chip">Live web search</div>
            <div class="chip">Groq reasoning</div>
            <div class="chip">Minimal chat surface</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Agent settings", expanded=False):
        settings_left, settings_right = st.columns([1, 1])
        temperature = settings_left.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
        max_results = settings_right.slider("Web results", 3, 8, 5, 1)
        clear_col, note_col = st.columns([1, 2])
        if clear_col.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_trace = []
            st.rerun()
        note_col.caption("Uses Groq for reasoning and Tavily for search.")

    st.markdown("<div class='card-title'>Quick prompts</div>", unsafe_allow_html=True)
    suggestions = [
        "What is the latest news about the global economy?",
        "Summarize the current state of AI regulation in the US.",
        "Find the latest release notes for Streamlit.",
    ]
    prompt_cols = st.columns(3)
    for index, prompt in enumerate(suggestions):
        with prompt_cols[index]:
            if st.button(prompt, key=f"suggestion::{prompt}", use_container_width=True):
                agent_executor = get_agent_executor(temperature, max_results)
                submit_prompt(prompt, agent_executor)
                st.rerun()

    try:
        agent_executor = get_agent_executor(temperature, max_results)
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
        st.stop()

    st.markdown("<div class='card-title'>Conversation</div>", unsafe_allow_html=True)

    if not st.session_state.messages:
        st.info("Ask something current or research-heavy")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.last_trace:
        with st.expander("Tool trace", expanded=False):
            st.markdown(trace_to_text(st.session_state.last_trace))

    prompt = st.chat_input("Ask something current or research-heavy...")

    if prompt:
        submit_prompt(prompt, agent_executor)
        st.rerun()


if __name__ == "__main__":
    main()
