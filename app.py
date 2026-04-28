import os
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import dotenv_values, load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from tavily import TavilyClient

APP_TITLE = "ReAct Research Agent"
APP_SUBTITLE = (
    "A lightweight LangChain agent that reasons step by step and uses Tavily web search "
    "whenever the answer may depend on recent or current information."
)
DEFAULT_MODEL = "openai/gpt-oss-120b"


def load_env_aliases() -> None:
    """Load the local .env file and mirror the key names this app expects."""
    env_path = Path(__file__).resolve().with_name(".env")
    load_dotenv(dotenv_path=env_path, override=False)
    env_values = dotenv_values(env_path)

    tavily_key = (
        os.getenv("TAVILY_API_KEY")
        or os.getenv("Tavily_API_KEY")
        or env_values.get("TAVILY_API_KEY")
        or env_values.get("Tavily_API_KEY")
    )
    groq_key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("Groq_API_KEY")
        or env_values.get("GROQ_API_KEY")
        or env_values.get("Groq_API_KEY")
    )

    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key
        os.environ["Tavily_API_KEY"] = tavily_key
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
        os.environ["Groq_API_KEY"] = groq_key


def format_history(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "No previous conversation."

    recent_messages = messages[-12:]
    lines: list[str] = []
    for message in recent_messages:
        role = message["role"]
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {message['content']}")
    return "\n".join(lines)


def build_prompt() -> ChatPromptTemplate:
    today = date.today().isoformat()
    system_template = """You are a concise, accurate research assistant.
Use the web_search tool for anything that may depend on current facts, recent events, live data, or verification.
If the tool does not provide enough evidence, say that you do not know.
Prefer the latest sourced information over memory.

When you decide to call a tool, use the tool-calling mechanism with JSON arguments. After you receive an observation from the tool, continue reasoning and call tools only when needed. When you are done, respond with:
Final Answer: <your answer>

Today is {today}.

You have access to the following tools:
{tools}

Tool names: {tool_names}
"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_template),
            ("system", "Conversation so far:\n{chat_history}"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    ).partial(today=today)


def build_web_search_tool(max_results: int = 5):
    @tool("web_search")
    def web_search(query: str) -> str:
        """Search the web for up-to-date information, news, facts, and verification."""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Tavily API key is missing. Set TAVILY_API_KEY or Tavily_API_KEY in the environment."

        client = TavilyClient(api_key=api_key)
        response: dict[str, Any] = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            search_depth="advanced",
        )

        sections: list[str] = []
        answer = response.get("answer")
        if answer:
            sections.append(f"Answer: {answer}")

        results = response.get("results", [])
        if not results:
            sections.append("No search results were returned.")
            return "\n\n".join(sections)

        for index, result in enumerate(results, start=1):
            title = result.get("title", "Untitled result")
            url = result.get("url", "")
            content = result.get("content", "")
            sections.append(f"{index}. {title}\nURL: {url}\nSnippet: {content}")

        return "\n\n".join(sections)

    return web_search


@st.cache_resource(show_spinner=False)
def build_agent(temperature: float, max_results: int):
    load_env_aliases()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Groq API key is missing. Set GROQ_API_KEY or Groq_API_KEY in the environment."
        )

    llm = ChatGroq(
        api_key=api_key,
        model_name=DEFAULT_MODEL,
        temperature=temperature,
        max_retries=2,
    )
    tools = [build_web_search_tool(max_results)]
    llm = llm.bind_tools(tools, tool_choice="auto")
    tools_desc = "\n".join(
        f"{tool_obj.name}: {tool_obj.description}" for tool_obj in tools
    )
    tool_names = ", ".join(tool_obj.name for tool_obj in tools)
    prompt = build_prompt().partial(tools=tools_desc, tool_names=tool_names)
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
        verbose=False,
        max_iterations=4,
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
            padding-top: 1rem;
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


def run_agent(agent_executor: AgentExecutor, prompt: str) -> tuple[str, list[Any]]:
    result = agent_executor.invoke(
        {
            "input": prompt,
            "chat_history": format_history(st.session_state.messages),
        }
    )
    output = str(result.get("output", "")).strip()
    intermediate_steps = result.get("intermediate_steps", [])
    return output, intermediate_steps


def trace_to_text(intermediate_steps: list[Any]) -> str:
    if not intermediate_steps:
        return "No tool calls were needed."

    lines: list[str] = []
    for index, (action, observation) in enumerate(intermediate_steps, start=1):
        tool_name = getattr(action, "tool", "unknown tool")
        tool_input = getattr(action, "tool_input", "")
        lines.append(f"Step {index}: {tool_name}")
        lines.append(f"Input: {tool_input}")
        lines.append(f"Observation: {observation}")
        lines.append("")
    return "\n".join(lines).rstrip()


def submit_prompt(prompt: str, agent_executor: AgentExecutor) -> None:
    if not prompt.strip():
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        with st.spinner("Researching the latest information..."):
            answer, trace = run_agent(agent_executor, prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_trace = trace
    except Exception as exc:  # noqa: BLE001
        error_message = f"I could not complete the request: {exc}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        st.session_state.last_trace = []


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🔎",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    load_env_aliases()
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
                agent_executor = build_agent(temperature, max_results)
                submit_prompt(prompt, agent_executor)
                st.rerun()

    try:
        agent_executor = build_agent(temperature, max_results)
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
        st.stop()

    st.markdown("<div class='card-title'>Conversation</div>", unsafe_allow_html=True)

    if not st.session_state.messages:
        st.info(
            "Ask something current or research-heavy. The agent will call web search when it needs live information."
        )

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
