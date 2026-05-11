from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import dotenv_values, load_dotenv


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    tavily_api_key: str | None
    # model_name: str = "openai/gpt-oss-120b"  # 8k TPM limit - too small for RAG
    model_name: str = "llama-3.3-70b-versatile"  # 12k TPM limit - better for RAG with context


def get_env_path() -> Path:
    root_dir = Path(__file__).resolve().parents[2]
    return root_dir / ".env"


def load_settings() -> Settings:
    env_path = get_env_path()
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

    return Settings(groq_api_key=groq_key, tavily_api_key=tavily_key)
