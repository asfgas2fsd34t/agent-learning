from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    base_url: str | None


class ConfigurationError(ValueError):
    pass


def load_settings() -> Settings:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or None

    if not api_key:
        raise ConfigurationError("缺少环境变量 LLM_API_KEY")
    if not model:
        raise ConfigurationError("缺少环境变量 LLM_MODEL")

    return Settings(api_key=api_key, model=model, base_url=base_url)
