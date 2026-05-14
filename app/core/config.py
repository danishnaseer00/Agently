from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import dotenv_values, load_dotenv


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    tavily_api_key: str | None
    supabase_url: str = ""
    supabase_key: str = ""
    clerk_jwks_url: str = ""
    clerk_secret_key: str = ""
    model_name: str = "llama-3.3-70b-versatile"
    deep_think_model: str = "llama-3.3-70b-versatile"


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
    supabase_url = (
        os.getenv("SUPABASE_URL")
        or env_values.get("SUPABASE_URL", "")
    )
    supabase_key = (
        os.getenv("SUPABASE_KEY")
        or env_values.get("SUPABASE_KEY", "")
    )
    clerk_jwks_url = (
        os.getenv("CLERK_JWKS_URL")
        or env_values.get("CLERK_JWKS_URL", "")
    )
    clerk_secret_key = (
        os.getenv("CLERK_SECRET_KEY")
        or env_values.get("CLERK_SECRET_KEY", "")
    )
    model_name = (
        os.getenv("MODEL_NAME")
        or env_values.get("MODEL_NAME", "llama-3.3-70b-versatile")
    )
    deep_think_model = (
        os.getenv("DEEP_THINK_MODEL")
        or env_values.get("DEEP_THINK_MODEL", "llama-3.3-70b-versatile")
    )

    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key
        os.environ["Tavily_API_KEY"] = tavily_key
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
        os.environ["Groq_API_KEY"] = groq_key

    return Settings(
        groq_api_key=groq_key,
        tavily_api_key=tavily_key,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        clerk_jwks_url=clerk_jwks_url,
        clerk_secret_key=clerk_secret_key,
        model_name=model_name,
        deep_think_model=deep_think_model,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached wrapper around load_settings()."""
    return load_settings()
