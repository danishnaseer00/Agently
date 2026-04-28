from __future__ import annotations

from datetime import date

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


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
