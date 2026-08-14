from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Settings
from .models import Paper


def paper_to_dict(paper: Paper, summary: dict[str, Any], pdf_path: Path | None, downloaded: bool) -> dict[str, Any]:
    return {
        "title": paper.title,
        "year": paper.year,
        "authors": paper.authors,
        "doi": paper.doi,
        "url": paper.url,
        "pdf_url": paper.pdf_url,
        "arxiv_id": paper.arxiv_id,
        "source": paper.source,
        "abstract": paper.abstract,
        "summary": summary,
        "pdf_path": str(pdf_path) if pdf_path else None,
        "downloaded": downloaded,
    }


def _abstract_md(paper: Paper) -> str:
    if not paper.abstract:
        return "_No abstract available._"
    text = paper.abstract.replace("\n", " ")
    if len(text) > 1200:
        text = text[:1200] + "…"
    return text


def _summary_md(summary: dict[str, Any]) -> str:
    lines = [
        f"- **主题 (Topic):** {summary.get('topic', 'N/A')}",
        f"- **策略 (Strategy):** {summary.get('strategy', 'N/A')}",
    ]
    key_points = summary.get("key_points") or []
    if key_points:
        points = "\n".join(f"  - {p}" for p in key_points)
        lines.append(f"- **关键点 (Key points):**\n{points}")
    if summary.get("warning"):
        lines.append(f"- ⚠️ {summary['warning']}")
    return "\n".join(lines)


def _paper_section(
    *,
    index: int | str,
    paper: Paper,
    summary: dict[str, Any],
    pdf_path: Path | None,
    downloaded: bool,
) -> str:
    lines = [
        f"## {index}. {paper.title}",
        "",
        f"- **年份:** {paper.year_str}",
        f"- **作者:** {paper.display_authors}",
        f"- **来源:** {paper.source}",
    ]
    if paper.doi:
        lines.append(f"- **DOI:** [{paper.doi}](https://doi.org/{paper.doi})")
    if paper.url:
        lines.append(f"- **链接:** {paper.url}")
    if paper.pdf_url:
        lines.append(f"- **PDF URL:** {paper.pdf_url}")
    if pdf_path:
        lines.append(f"- **本地文件:** `{pdf_path}`")
        lines.append(f"- **下载状态:** ✅ 已下载")
    else:
        lines.append(f"- **下载状态:** ❌ 未能下载（可能不是开放获取）")
    lines += [
        "",
        "### 摘要",
        "",
        _abstract_md(paper),
        "",
        "### 简要整理",
        "",
        _summary_md(summary),
        "",
    ]
    return "\n".join(lines)


def write_report(
    main_paper: Paper,
    main_summary: dict[str, Any],
    main_pdf: Path | None,
    main_downloaded: bool,
    ref_runs: list[dict[str, Any]],
    settings: Settings,
) -> Path:
    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.md"

    lines = [
        "# paper_go 报告",
        "",
        f"- **查询:** {main_paper.title}",
        f"- **输出目录:** `{output_dir}`",
        f"- **引用论文数:** {len(ref_runs)}",
        "",
    ]

    lines.append(_paper_section(
        index="目标论文",
        paper=main_paper,
        summary=main_summary,
        pdf_path=main_pdf,
        downloaded=main_downloaded,
    ))

    lines.append("---")
    lines.append("")
    lines.append(f"## 参考文献 ({len(ref_runs)})")
    lines.append("")
    if not ref_runs:
        lines.append("_未获取到参考文献列表。_")
    else:
        for idx, run in enumerate(ref_runs, start=1):
            lines.append(_paper_section(
                index=idx,
                paper=run["paper"],
                summary=run["summary"],
                pdf_path=run["pdf_path"],
                downloaded=run["downloaded"],
            ))
            lines.append("---")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
