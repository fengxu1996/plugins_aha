from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import Settings
from .engine import run_paper_go


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper_go",
        description="下载指定论文及其引用论文，并整理每篇论文的摘要、主题和策略。",
    )
    parser.add_argument("query", help="论文标题、DOI、arXiv ID 或 URL")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认 paper_go_output）")
    parser.add_argument("--max-references", type=int, default=None, help="最多获取的引用论文数（默认 20）")
    parser.add_argument("--llm-api-key", default=None, help="OpenAI 兼容 API Key；也可用环境变量 PAPER_GO_API_KEY")
    parser.add_argument("--llm-base-url", default=None, help="OpenAI 兼容 API Base URL")
    parser.add_argument("--llm-model", default=None, help="LLM 模型名称")
    parser.add_argument("--no-download", action="store_true", help="只获取元数据并生成摘要，不下载 PDF")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()

    if args.output_dir:
        settings.output_dir = Path(args.output_dir)
    if args.max_references is not None:
        settings.max_references = args.max_references
    if args.llm_api_key:
        settings.api_key = args.llm_api_key
    if args.llm_base_url:
        settings.llm_base_url = args.llm_base_url
    if args.llm_model:
        settings.llm_model = args.llm_model

    try:
        result = run_paper_go(args.query, settings=settings, download=not args.no_download)
    except Exception as exc:
        print(f"❌ paper_go 执行失败：{exc}", file=sys.stderr)
        return 1

    refs = result["references"]
    downloaded_main = result["downloaded"]
    downloaded_refs = sum(1 for r in refs if r.downloaded)
    print("✅ paper_go 执行完成")
    print(f"  目标论文：{result['paper'].title}")
    print(f"  输出目录：{result['output_dir']}")
    print(f"  报告文件：{result['report_path']}")
    print(f"  目标论文 PDF：{'✅' if downloaded_main else '❌'}")
    print(f"  引用论文：{len(refs)} 篇，成功下载 {downloaded_refs} 篇")
    if not downloaded_main and not downloaded_refs:
        print("  提示：很多论文不是开放获取，未能自动下载 PDF。可设置 Unpaywall email 提高成功率。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
