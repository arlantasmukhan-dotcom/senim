"""Runtime settings, read from environment variables (and a local .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)  # .env always wins over a stray shell env var


# Models the user can pick as "the AI that wrote this answer" (Phantom Twin sensor). Only these are
# accepted from requests, so nobody can make the server call an arbitrary (expensive) model.
AUTHOR_MODELS = [
    {"id": "openai/gpt-6-luna", "label": "ChatGPT"},
    {"id": "google/gemini-3.5-flash-lite", "label": "Gemini"},
    {"id": "anthropic/claude-haiku-4.5", "label": "Claude"},
    {"id": "deepseek/deepseek-v4-flash", "label": "DeepSeek"},
]


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
    llm_concurrency: int = 8           # parallel model calls within one check
    llm_global_concurrency: int = 48   # parallel model calls across all checks in this process
    rate_limit_per_hour: int = 20      # checks per client IP per hour; 0 = off
    daily_budget_usd: float = 10.0     # stop accepting checks once today's model spend reaches this; 0 = off
    cascade: bool = True               # skip the witness sensors when the sources already settle a claim
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
    s.llm_concurrency = int(env.get("SENIM_LLM_CONCURRENCY", s.llm_concurrency))
    s.llm_global_concurrency = int(env.get("SENIM_LLM_GLOBAL_CONCURRENCY", s.llm_global_concurrency))
    s.rate_limit_per_hour = int(env.get("SENIM_RATE_LIMIT_PER_HOUR", s.rate_limit_per_hour))
    s.daily_budget_usd = float(env.get("SENIM_DAILY_BUDGET_USD", s.daily_budget_usd))
    s.cascade = env.get("SENIM_CASCADE", "1").strip() not in ("0", "false", "off")
    return s


settings = load_settings()
