from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, Optional, Set, Tuple

import aiohttp

from .config import Settings
from .link_utils import extract_links
from .file_detector import is_downloadable_url
from .downloader import fetch_html, download_file
from .ai_reasoner import combined_score
from .db import AcquisitionRecord, init_db, insert_metadata, get_engine


@dataclass
class QueueItem:
    url: str
    depth: int
    priority: float


class Crawler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.visited_pages: Set[str] = set()
        self.engine = get_engine()
        init_db(self.engine)
        self._queue: asyncio.PriorityQueue[Tuple[float, QueueItem]] = asyncio.PriorityQueue()
        self._host_semaphores: Dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(self.settings.per_host_concurrency)
        )
        self._stats: Dict[str, int] = defaultdict(int)  # fetched_pages, downloaded_files, errors

    @property
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

    async def run(self, start_url: str) -> None:
        headers = {"User-Agent": self.settings.user_agent}
        timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout_seconds)
        connector = aiohttp.TCPConnector(limit=None)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector) as session:
            await self._submit(QueueItem(url=start_url, depth=0, priority=0.0))
            workers = [asyncio.create_task(self._worker(session)) for _ in range(self.settings.max_concurrency)]
            await self._queue.join()
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

    async def _submit(self, item: QueueItem) -> None:
        await self._queue.put((-item.priority, item))

    async def _worker(self, session: aiohttp.ClientSession) -> None:
        while True:
            try:
                _, item = await self._queue.get()
                await self._process_item(session, item)
            except asyncio.CancelledError:
                break
            except Exception:
                self._stats["errors"] += 1
            finally:
                self._queue.task_done()

    async def _process_item(self, session: aiohttp.ClientSession, item: QueueItem) -> None:
        if item.url in self.visited_pages:
            return
        self.visited_pages.add(item.url)

        # Per-host throttle
        from urllib.parse import urlsplit

        host = urlsplit(item.url).netloc
        host_sem = self._host_semaphores[host]
        async with host_sem:
            try:
                html = await fetch_html(session, item.url, self.settings.request_timeout_seconds)
                self._stats["fetched_pages"] += 1
            except Exception:
                self._stats["errors"] += 1
                return

        score = combined_score(html, item.url, self.settings.enable_ai, self.settings.ai_model)
        links = extract_links(html, item.url)

        for href in links:
            if is_downloadable_url(href):
                await self._download_and_log(session, href, item.depth + 1, self.settings.output_dir)
            elif item.depth + 1 <= self.settings.max_depth and href not in self.visited_pages:
                await self._submit(QueueItem(url=href, depth=item.depth + 1, priority=score))

    async def _download_and_log(
        self,
        session: aiohttp.ClientSession,
        url: str,
        depth: int,
        output_dir: Path,
    ) -> None:
        try:
            dest, content_type, size_kb = await download_file(
                session,
                url,
                output_dir,
                self.settings.request_timeout_seconds,
                max_file_size_kb=self.settings.max_file_size_kb,
                max_retries=self.settings.max_retries,
                backoff_base_seconds=self.settings.backoff_base_seconds,
            )
            record = AcquisitionRecord(
                url=url,
                file_name=str(dest.name),
                depth=depth,
                content_type=content_type,
                file_size_kb=size_kb,
                ai_score=None,
                timestamp=datetime.utcnow(),
            )
            insert_metadata(record, engine=self.engine)
            self._stats["downloaded_files"] += 1
        except Exception:
            self._stats["errors"] += 1
            return
