from __future__ import annotations

import os
import re
from typing import Optional


def heuristic_score(html_text: str, url: str) -> float:
    text = (html_text or "")[:200_000].lower()
    url_lower = (url or "").lower()
    keywords = [
        "dataset",
        "data",
        "download",
        "csv",
        "xlsx",
        "json",
        "statistics",
        "report",
        "api",
        "resource",
        "catalog",
        "open data",
        "indicator",
        "time series",
    ]
    score = 0.0
    for kw in keywords:
        score += text.count(kw) * 0.5
        if kw in url_lower:
            score += 1.0
    # Penalize obvious non-content pages
    penalties = ["login", "signin", "javascript:"]
    for p in penalties:
        if p in text or p in url_lower:
            score -= 1.0
    return max(0.0, min(score, 100.0))


def ai_score_html(html_text: str, model: str = "gpt-4o-mini") -> Optional[float]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = (
            "You are ranking web pages for likelihood of containing downloadable datasets. "
            "Given the HTML snippet, respond with ONLY a number from 0 to 100, where 100 is very likely."
        )
        content = html_text[:8000]
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.0,
            max_tokens=4,
        )
        text = resp.choices[0].message.content.strip()
        m = re.search(r"(\d{1,3})", text)
        if not m:
            return None
        val = float(m.group(1))
        return max(0.0, min(val, 100.0))
    except Exception:
        return None


def combined_score(html_text: str, url: str, enable_ai: bool, model: str) -> float:
    base = heuristic_score(html_text, url)
    if not enable_ai:
        return base
    ai = ai_score_html(html_text, model=model)
    if ai is None:
        return base
    # Blend: 70% heuristic, 30% AI
    return 0.7 * base + 0.3 * ai
