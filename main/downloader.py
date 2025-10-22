from __future__ import annotations

import asyncio
import hashlib
import math
from pathlib import Path
from typing import Optional, Tuple

import aiohttp


class DownloadError(Exception):
    pass


_DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,\n        image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def head_request(session: aiohttp.ClientSession, url: str, timeout_seconds: int) -> Optional[aiohttp.ClientResponse]:
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with session.head(url, timeout=timeout, allow_redirects=True, headers=_DEFAULT_HEADERS) as resp:
            return resp
    except Exception:
        return None


async def fetch_html(session: aiohttp.ClientSession, url: str, timeout_seconds: int) -> str:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    async with session.get(url, timeout=timeout, headers=_DEFAULT_HEADERS) as resp:
        resp.raise_for_status()
        return await resp.text(errors="ignore")


def _safe_filename_from_url(url: str, fallback_ext: str = "") -> str:
    try:
        from urllib.parse import urlsplit

        parts = urlsplit(url)
        name = Path(parts.path).name
        if name and len(name) <= 200:
            return name
    except Exception:
        pass
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"download_{digest}{fallback_ext}"


async def download_file(
    session: aiohttp.ClientSession,
    url: str,
    output_dir: Path,
    timeout_seconds: int,
    max_file_size_kb: int = 51200,
    max_retries: int = 3,
    backoff_base_seconds: float = 0.5,
) -> Tuple[Path, Optional[str], float]:
    output_dir.mkdir(parents=True, exist_ok=True)

    head_resp = await head_request(session, url, timeout_seconds)
    if head_resp is not None:
        try:
            head_resp.raise_for_status()
        except Exception:
            pass
        content_length = head_resp.headers.get("Content-Length") if head_resp else None
        if content_length is not None:
            try:
                size_bytes = int(content_length)
                if size_bytes > max_file_size_kb * 1024:
                    raise DownloadError("File too large by preflight check")
            except Exception:
                pass

    attempt = 0
    while True:
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with session.get(url, timeout=timeout, headers=_DEFAULT_HEADERS) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type")
                content_length = resp.headers.get("Content-Length")
                if content_length is not None:
                    try:
                        if int(content_length) > max_file_size_kb * 1024:
                            raise DownloadError("File too large (content-length)")
                    except Exception:
                        pass
                filename = _safe_filename_from_url(url)
                dest = output_dir / filename
                counter = 1
                while dest.exists() and counter < 1000:
                    dest = output_dir / f"{dest.stem}_{counter}{dest.suffix}"
                    counter += 1
                size_bytes = 0
                with dest.open("wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 64):
                        if chunk:
                            f.write(chunk)
                            size_bytes += len(chunk)
                            if size_bytes > max_file_size_kb * 1024:
                                raise DownloadError("File too large (stream)")
                size_kb = round(size_bytes / 1024.0, 3)
                return dest, content_type, size_kb
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise
            delay = backoff_base_seconds * (2 ** (attempt - 1))
            await asyncio.sleep(min(delay, 10))
