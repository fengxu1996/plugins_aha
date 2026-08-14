from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import apis
from .config import Settings
from .models import Paper
from .report import paper_to_dict, write_report
from .summary import summarize_paper
from .utils import HTTPClient, safe_filename, write_json


@dataclass
class PaperRun:
    paper: Paper
    summary: dict[str, Any] = field(default_factory=dict)
    pdf_path: Path | None = None
    downloaded: bool = False
    download_error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return paper_to_dict(
            self.paper,
            self.summary,
            self.pdf_path,
            self.downloaded,
        )


def _dedupe(papers: list[Paper]) -> list[Paper]:
    seen: set[str] = set()
    result: list[Paper] = []
    for p in papers:
        key = (p.doi or "").lower() or p.title.strip().lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(p)
    return result


def _download_one(
    paper: Paper,
    dest: Path,
    client: HTTPClient,
    settings: Settings,
) -> tuple[Path | None, bool, str | None]:
    try:
        ok = apis.download_pdf(paper, dest, client, settings.unpaywall_email)
        if ok:
            return dest, True, None
        return None, False, "No open-access PDF found or download failed."
    except Exception as exc:
        return None, False, str(exc)


def run_paper_go(
    query: str,
    settings: Settings | None = None,
    download: bool = True,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    client = HTTPClient(timeout=settings.timeout, user_agent=settings.user_agent)

    main_paper = apis.search_paper(query, client)
    output_dir = settings.output_dir / main_paper.slug
    output_dir.mkdir(parents=True, exist_ok=True)

    main_summary = summarize_paper(main_paper, settings)
    main_pdf_path: Path | None = None
    main_downloaded = False
    main_error: str | None = None
    if download:
        main_pdf_path, main_downloaded, main_error = _download_one(
            main_paper,
            output_dir / "main.pdf",
            client,
            settings,
        )
        if main_error:
            main_summary["download_warning"] = main_error
    else:
        main_summary["download_warning"] = "Skipped by --no-download."

    refs = _dedupe(apis.references_for(main_paper, client, settings.max_references))
    ref_runs: list[PaperRun] = []

    refs_dir = output_dir / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)

    for idx, ref in enumerate(refs, start=1):
        ref_summary = summarize_paper(ref, settings)
        pdf_path: Path | None = None
        downloaded = False
        error: str | None = None
        if download:
            filename = f"{idx:02d}-{safe_filename(ref.slug)}.pdf"
            pdf_path, downloaded, error = _download_one(
                ref,
                refs_dir / filename,
                client,
                settings,
            )
        else:
            error = "Skipped by --no-download."
        if error:
            ref_summary["download_warning"] = error
        ref_runs.append(
            PaperRun(
                paper=ref,
                summary=ref_summary,
                pdf_path=pdf_path,
                downloaded=downloaded,
                download_error=error,
            )
        )

    report_path = write_report(
        main_paper=main_paper,
        main_summary=main_summary,
        main_pdf=main_pdf_path,
        main_downloaded=main_downloaded,
        ref_runs=[
            {
                "paper": r.paper,
                "summary": r.summary,
                "pdf_path": r.pdf_path,
                "downloaded": r.downloaded,
            }
            for r in ref_runs
        ],
        settings=settings,
    )

    payload = {
        "query": query,
        "main_paper": {},
        "main_summary": main_summary,
        "main_pdf": str(main_pdf_path) if main_pdf_path else None,
        "main_downloaded": main_downloaded,
        "references": [r.as_dict() for r in ref_runs],
        "report_path": str(report_path),
        "output_dir": str(output_dir),
    }
    # Make sure main_paper.as_dict() includes summary/PDF info via paper_to_dict too.
    payload["main_paper"] = paper_to_dict(
        main_paper,
        main_summary,
        main_pdf_path,
        main_downloaded,
    )
    write_json(output_dir / "papers.json", payload)

    result = {
        "query": query,
        "paper": main_paper,
        "summary": main_summary,
        "pdf_path": main_pdf_path,
        "downloaded": main_downloaded,
        "references": ref_runs,
        "report_path": report_path,
        "output_dir": output_dir,
    }
    return result
