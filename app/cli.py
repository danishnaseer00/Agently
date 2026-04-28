from __future__ import annotations

import argparse

from app.agent.agent import build_agent
from app.agent.executor import run_agent
from app.core.config import load_settings
from app.core.llm import build_llm
from app.tools.search import build_web_search_tool


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ReAct agent from the CLI")
    parser.add_argument("query", help="Question to ask")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-results", type=int, default=5)
    args = parser.parse_args()

    settings = load_settings()
    tools = [build_web_search_tool(settings, args.max_results)]
    llm = build_llm(settings, args.temperature, tools)
    agent_executor = build_agent(llm, tools)
    answer, _ = run_agent(agent_executor, args.query, "No previous conversation.")
    print(answer)


if __name__ == "__main__":
    main()
