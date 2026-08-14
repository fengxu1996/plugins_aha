from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Paper:
    """Normalized metadata for one paper."""

    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    authors: list[str] = field(default_factory=list)
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    arxiv_id: Optional[str] = None
    source: str = "unknown"
    external_ids: dict[str, str] = field(default_factory=dict)
    references: list["Paper"] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        """A filesystem-safe short identifier."""
        import re
        base = re.sub(r"[^\w\u4e00-\u9fff]+", "-", self.title.strip().lower())
        base = re.sub(r"-+", "-", base).strip("-")
        return (base[:80] or "paper").strip()

    @property
    def display_authors(self) -> str:
        if not self.authors:
            return "Unknown"
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return f"{self.authors[0]} et al."

    @property
    def year_str(self) -> str:
        return str(self.year) if self.year else "n.d."
