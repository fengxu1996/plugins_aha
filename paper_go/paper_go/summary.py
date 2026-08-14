from __future__ import annotations

import json
import re

from .config import Settings
from .models import Paper


_LOCAL_CUES = (
    "we propose", "we introduce", "we present", "we develop", "we design",
    "we use", "we apply", "we conduct", "we evaluate", "we show", "we study",
    "we investigate", "we compare", "we build", "we implement", "we release",
    "this paper", "this work", "method", "approach", "framework", "model",
    "experiment", "evaluation", "architecture", "algorithm", "dataset",
)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def local_summary(paper: Paper) -> dict[str, object]:
    title = paper.title or "Untitled"
    abstract = paper.abstract
    if not abstract:
        return {
            "topic": title,
            "strategy": "No abstract available; please open the PDF for details.",
            "key_points": [],
            "summary": f"论文标题：{title}（暂无摘要）",
        }

    sentences = _sentences(abstract)
    topic_sentences = sentences[:2]
    topic = " ".join(topic_sentences) if topic_sentences else abstract[:200]

    strategy_sentences = []
    for sent in sentences:
        if any(cue in sent.lower() for cue in _LOCAL_CUES):
            strategy_sentences.append(sent)
        if len(strategy_sentences) >= 3:
            break
    if not strategy_sentences:
        strategy_sentences = sentences[:2]
    strategy = " ".join(strategy_sentences)

    key_points = sentences[:3]
    return {
        "topic": topic,
        "strategy": strategy,
        "key_points": key_points,
        "summary": f"主题：{topic}\n策略：{strategy}",
    }


def llm_summary(paper: Paper, settings: Settings) -> dict[str, object]:
    """Use an OpenAI-compatible chat completions endpoint for a concise summary."""
    if not settings.api_key:
        return local_summary(paper)

    abstract = paper.abstract or "No abstract available."
    prompt = f"""You are a research assistant. Given the following paper title and abstract, output a JSON object with exactly these keys:
- "topic": a short Chinese phrase describing the research topic
- "strategy": a short Chinese sentence describing the core method/strategy
- "key_points": an array of 2-4 Chinese bullet strings for important contributions
- "summary": 2-3 Chinese sentences summarizing the paper

Paper title: {paper.title}
Abstract: {abstract[:4000]}

Return only valid JSON, no markdown fences.
"""
    url = settings.llm_base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    import requests

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": "You are a precise research summarizer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=settings.timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        obj = json.loads(content)
        return {
            "topic": obj.get("topic", local_summary(paper)["topic"]),
            "strategy": obj.get("strategy", local_summary(paper)["strategy"]),
            "key_points": obj.get("key_points", []),
            "summary": obj.get("summary", local_summary(paper)["summary"]),
        }
    except Exception as exc:
        result = local_summary(paper)
        result["warning"] = f"LLM summarization failed ({exc}); used built-in extractive summary."
        return result


def summarize_paper(paper: Paper, settings: Settings) -> dict[str, object]:
    if settings.api_key:
        return llm_summary(paper, settings)
    return local_summary(paper)
