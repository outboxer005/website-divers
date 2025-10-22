from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .config import Settings, load_settings
from .crawler import Crawler
from .db import get_latest_records, init_db, clear_all_records

app = FastAPI(title="Lally Data Acquisition UI")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Global crawl state
_is_crawling = False
_state_lock = asyncio.Lock()
_current_stats: dict[str, int] = {}
_current_settings: Optional[Settings] = None
_recent_errors: list[str] = []


@app.on_event("startup")
async def on_startup() -> None:
    init_db()


@app.get("/status")
async def status() -> JSONResponse:
    data = {
        "crawling": _is_crawling,
        "stats": _current_stats,
        "errors": _recent_errors[-5:],
        "settings": {
            "max_depth": _current_settings.max_depth if _current_settings else None,
            "max_concurrency": _current_settings.max_concurrency if _current_settings else None,
            "per_host_concurrency": _current_settings.per_host_concurrency if _current_settings else None,
        },
    }
    return JSONResponse(data)


@app.post("/clear")
async def clear() -> RedirectResponse:
    clear_all_records()
    return RedirectResponse(url="/", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    records = get_latest_records(limit=50)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "records": records,
        },
    )


@app.post("/crawl")
async def crawl(
    request: Request,
    url: str = Form(...),
    depth: int = Form(2),
    concurrency: int = Form(8),
    per_host: int = Form(2),
    enable_ai: bool = Form(False),
    ai_model: str = Form("gpt-4o-mini"),
):
    global _is_crawling, _current_stats, _current_settings, _recent_errors
    async with _state_lock:
        if _is_crawling:
            return RedirectResponse(url="/", status_code=303)
        _is_crawling = True
        _recent_errors = []

    base = load_settings()
    settings = Settings(
        start_url=url,
        max_depth=depth,
        max_concurrency=concurrency,
        per_host_concurrency=per_host,
        output_dir=base.output_dir,
        db_url=base.db_url,
        enable_ai=enable_ai,
        ai_model=ai_model,
        request_timeout_seconds=base.request_timeout_seconds,
        user_agent=base.user_agent,
        respect_robots=base.respect_robots,
        max_file_size_kb=base.max_file_size_kb,
        max_retries=base.max_retries,
        backoff_base_seconds=base.backoff_base_seconds,
        allow_render_js=base.allow_render_js,
    )
    _current_settings = settings

    async def _run_and_reset():
        global _is_crawling, _current_stats, _recent_errors
        try:
            crawler = Crawler(settings)
            await crawler.run(url)
            _current_stats = crawler.stats
        except Exception as e:
            _recent_errors.append(str(e)[:300])
        finally:
            _is_crawling = False

    asyncio.create_task(_run_and_reset())
    return RedirectResponse(url="/", status_code=303)
