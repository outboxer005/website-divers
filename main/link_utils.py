from __future__ import annotations

from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup


def normalize_url(base_url: str, href: str) -> Optional[str]:
    if not href:
        return None
    if href.startswith("javascript:") or href.startswith("mailto:"):
        return None
    absolute = urljoin(base_url, href)
    parts = urlsplit(absolute)
    if parts.scheme not in {"http", "https"}:
        return None
    # Drop fragments
    clean = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
    return clean


def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    links: List[str] = []
    for a in soup.find_all("a"):
        href = a.get("href")
        normalized = normalize_url(base_url, href)
        if normalized:
            links.append(normalized)
    return links
