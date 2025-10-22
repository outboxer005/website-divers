from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except Exception:
        return default


def _to_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    start_url: str | None = None
    max_depth: int = 2
    max_concurrency: int = 8
    per_host_concurrency: int = 2
    output_dir: Path = Path("downloads")

    # Database
    db_url: str | None = None

    # AI controls
    enable_ai: bool = False
    ai_model: str = "gpt-4o-mini"

    # Networking / crawling
    request_timeout_seconds: int = 20
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    respect_robots: bool = True
    max_file_size_kb: int = 51200  # 50 MB
    max_retries: int = 3
    backoff_base_seconds: float = 0.5
    allow_render_js: bool = False  # placeholder, not implemented


def load_settings() -> Settings:
    start_url = os.environ.get("START_URL")
    max_depth = _to_int(os.environ.get("MAX_DEPTH"), 2)
    max_concurrency = _to_int(os.environ.get("MAX_CONCURRENCY"), 8)
    per_host_concurrency = _to_int(os.environ.get("PER_HOST_CONCURRENCY"), 2)
    output_dir = Path(os.environ.get("OUTPUT_DIR", "downloads")).resolve()

    db_url = os.environ.get("DB_URL")

    enable_ai = _to_bool(os.environ.get("ENABLE_AI"), False)
    ai_model = os.environ.get("AI_MODEL", "gpt-4o-mini")

    request_timeout_seconds = _to_int(os.environ.get("REQUEST_TIMEOUT_SECONDS"), 20)
    user_agent = os.environ.get(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    )

    respect_robots = _to_bool(os.environ.get("RESPECT_ROBOTS"), True)
    max_file_size_kb = _to_int(os.environ.get("MAX_FILE_SIZE_KB"), 51200)
    max_retries = _to_int(os.environ.get("MAX_RETRIES"), 3)
    backoff_base_seconds = _to_float(os.environ.get("BACKOFF_BASE_SECONDS"), 0.5)
    allow_render_js = _to_bool(os.environ.get("ALLOW_RENDER_JS"), False)

    return Settings(
        start_url=start_url,
        max_depth=max_depth,
        max_concurrency=max_concurrency,
        per_host_concurrency=per_host_concurrency,
        output_dir=output_dir,
        db_url=db_url,
        enable_ai=enable_ai,
        ai_model=ai_model,
        request_timeout_seconds=request_timeout_seconds,
        user_agent=user_agent,
        respect_robots=respect_robots,
        max_file_size_kb=max_file_size_kb,
        max_retries=max_retries,
        backoff_base_seconds=backoff_base_seconds,
        allow_render_js=allow_render_js,
    )
