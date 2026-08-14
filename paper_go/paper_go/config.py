from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

def _load_dotenv_file(path: Path) -> None:
    """A tiny .env loader so paper_go works without python-dotenv installed."""
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def load_env_file(path: Optional[str | Path] = None) -> None:
    """Load .env files using a built-in parser (no third-party dependency)."""
    if path is not None:
        _load_dotenv_file(Path(path))
    else:
        _load_dotenv_file(Path.cwd() / ".env")
        _load_dotenv_file(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Settings:
    """Runtime configuration for paper_go.

    All values can be provided via environment variables or a .env file.
    """

    api_key: Optional[str] = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    max_references: int = 20
    output_dir: Path = field(default_factory=lambda: Path("paper_go_output"))
    timeout: int = 30
    user_agent: str = "paper_go/0.1 (mailto:example@example.com)"
    unpaywall_email: Optional[str] = None

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)

    @classmethod
    def from_env(cls) -> "Settings":
        load_env_file()
        api_key = (
            os.getenv("PAPER_GO_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or None
        )
        output_dir = Path(os.getenv("PAPER_GO_OUTPUT_DIR", "paper_go_output"))
        max_refs = int(os.getenv("PAPER_GO_MAX_REFERENCES", "20"))
        timeout = int(os.getenv("PAPER_GO_TIMEOUT", "30"))
        return cls(
            api_key=api_key,
            llm_base_url=os.getenv("PAPER_GO_LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_model=os.getenv("PAPER_GO_LLM_MODEL", "gpt-4o-mini"),
            max_references=max_refs,
            output_dir=output_dir,
            timeout=timeout,
            user_agent=os.getenv(
                "PAPER_GO_USER_AGENT",
                "paper_go/0.1 (mailto:example@example.com)",
            ),
            unpaywall_email=os.getenv("PAPER_GO_UNPAYWALL_EMAIL") or None,
        )
