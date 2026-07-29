from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    base_url: str | None


def load_settings() -> Settings:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or None
    if not api_key or not model:
        raise ValueError("缺少 LLM_API_KEY 或 LLM_MODEL")
    return Settings(api_key=api_key, model=model, base_url=base_url)

