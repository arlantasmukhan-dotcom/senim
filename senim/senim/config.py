"""Runtime settings, read from environment variables (and a local .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)  # .env always wins over a stray shell env var


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class Settings:
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    model_main: str = "anthropic/claude-sonnet-5"
    model_fast: str = "anthropic/claude-haiku-4.5"
    witnesses: list[str] = field(
        default_factory=lambda: [
            "openai/gpt-6-luna",
            "google/gemini-3.5-flash-lite",
            "deepseek/deepseek-v4-flash",
        ]
    )
    contact_email: str = ""
    max_claims: int = 12
    max_input_chars: int = 8000
    llm_concurrency: int = 8
    http_timeout: float = 20.0

    @property
    def has_llm(self) -> bool:
        return bool(self.openrouter_api_key)

    @property
    def has_search(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def user_agent(self) -> str:
        contact = f"; {self.contact_email}" if self.contact_email else ""
        return f"SENIM/0.1 (AI answer checker; https://github.com/yv7m8fchnb-dev/Wit-teens{contact})"


def load_settings() -> Settings:
    env = os.environ
    s = Settings(
        openrouter_api_key=env.get("OPENROUTER_API_KEY", "").strip(),
        tavily_api_key=env.get("TAVILY_API_KEY", "").strip(),
        contact_email=env.get("SENIM_CONTACT_EMAIL", "").strip(),
    )
    s.model_main = env.get("SENIM_MODEL_MAIN", s.model_main).strip() or s.model_main
    s.model_fast = env.get("SENIM_MODEL_FAST", s.model_fast).strip() or s.model_fast
    if env.get("SENIM_WITNESSES", "").strip():
        s.witnesses = _csv(env["SENIM_WITNESSES"])
    s.max_claims = int(env.get("SENIM_MAX_CLAIMS", s.max_claims))
    s.max_input_chars = int(env.get("SENIM_MAX_INPUT_CHARS", s.max_input_chars))
    return s


settings = load_settings()
