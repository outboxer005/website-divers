from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich import print

from .config import Settings, load_settings
from .crawler import Crawler
from .db import init_db

app = typer.Typer(add_completion=False, help="AI-Based Data Acquisition Agent")


@app.command()
def crawl(
    url: str = typer.Option(..., "--url", help="Starting landing URL"),
    depth: int = typer.Option(2, "--depth", min=0, help="Crawl depth (0..3)"),
    concurrency: int = typer.Option(8, "--concurrency", min=1, help="Max concurrent downloads"),
    output: Path = typer.Option(Path("downloads"), "--output", help="Directory to store downloads"),
    enable_ai: bool = typer.Option(False, "--enable-ai", help="Enable AI page prioritization"),
    ai_model: str = typer.Option("gpt-4o-mini", "--ai-model", help="AI model if --enable-ai"),
):
    settings = load_settings()
    settings = Settings(
        start_url=url,
        max_depth=depth,
        max_concurrency=concurrency,
        output_dir=output.resolve(),
        db_url=settings.db_url,
        enable_ai=enable_ai,
        ai_model=ai_model,
        request_timeout_seconds=settings.request_timeout_seconds,
        user_agent=settings.user_agent,
    )

    print(f"[bold green]Starting crawl[/bold green]: {url} (depth={depth}, concurrency={concurrency})")
    crawler = Crawler(settings)
    asyncio.run(crawler.run(url))


if __name__ == "__main__":  # pragma: no cover
    app()
