from __future__ import annotations

import mimetypes
from typing import Optional

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".zip",
    ".pdf",
    ".xml",
    ".parquet",
    ".txt",
    ".gz",
    ".tar",
}

# Ensure common types are known
mimetypes.init()


def is_downloadable_url(url: str, content_type_hint: Optional[str] = None) -> bool:
    content_type = content_type_hint or guess_mime_from_url(url)
    if content_type:
        if any(
            content_type.startswith(prefix)
            for prefix in (
                "text/csv",
                "application/json",
                "application/pdf",
                "application/zip",
                "application/x-zip-compressed",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/plain",
                "application/xml",
                "application/x-tar",
                "application/gzip",
                "application/octet-stream",
            )
        ):
            return True
    # Fallback to extension check
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def guess_mime_from_url(url: str) -> Optional[str]:
    mime, _ = mimetypes.guess_type(url)
    return mime
