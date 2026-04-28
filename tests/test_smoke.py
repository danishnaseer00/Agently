from __future__ import annotations

import unittest

from app.agent.agent import build_agent
from app.agent.parser import build_prompt
from app.core.config import load_settings
from app.core.llm import build_llm
from app.tools.search import build_web_search_tool


class SmokeTests(unittest.TestCase):
    def test_prompt_builds(self) -> None:
        prompt = build_prompt()
        self.assertIsNotNone(prompt)

    def test_agent_builds_if_keys(self) -> None:
        settings = load_settings()
        if not settings.groq_api_key:
            self.skipTest("Missing GROQ_API_KEY")
        tools = [build_web_search_tool(settings, 1)]
        llm = build_llm(settings, 0.0, tools)
        executor = build_agent(llm, tools, max_iterations=1)
        self.assertIsNotNone(executor)


if __name__ == "__main__":
    unittest.main()
