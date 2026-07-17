from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    base_url: str | None


class ConfigurationError(ValueError):
    """Raised when required LLM configuration is missing."""


def load_settings() -> Settings:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        raise ConfigurationError("缺少环境变量 LLM_API_KEY")

    model = os.getenv("LLM_MODEL", "").strip()
    if not model:
        raise ConfigurationError("缺少环境变量 LLM_MODEL")

    base_url = os.getenv("LLM_BASE_URL", "").strip() or None
    return Settings(api_key=api_key, model=model, base_url=base_url)
