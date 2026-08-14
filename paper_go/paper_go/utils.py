from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

import requests


class HTTPClient:
    """Small shared HTTP client with retries and sensible headers."""

    def __init__(self, timeout: int = 30, user_agent: str = "paper_go/0.1"):
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get(
        self,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> requests.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(retries):
            try:
                resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                return resp
            except Exception as exc:  # requests.RequestException
                last_exc = exc
                if attempt < retries - 1:
                    time.sleep(backoff * (2**attempt))
        raise RuntimeError(f"GET {url} failed after {retries} attempts: {last_exc}")


def reconstruct_abstract(inverted_index: Optional[dict[str, list[int]]]) -> Optional[str]:
    """Reconstruct OpenAlex's inverted-index abstract into plain text."""
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for word, indices in inverted_index.items():
        for idx in indices:
            positions[idx] = word
    if not positions:
        return None
    max_pos = max(positions)
    return " ".join(positions.get(i, "") for i in range(max_pos + 1)).strip() or None


def clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def safe_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r'[\\/:*?"<>|]+', "_", name).strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return (name[:max_len] or "paper").rstrip(".")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
