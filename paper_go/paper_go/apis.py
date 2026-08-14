from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Iterable, Optional

from .models import Paper
from .utils import HTTPClient, clean_text, reconstruct_abstract

CROSSREF_API = "https://api.crossref.org/works"
SEMANTIC_API = "https://api.semanticscholar.org/graph/v1"
OPENALEX_API = "https://api.openalex.org/works"
ARXIV_API = "https://export.arxiv.org/api/query"
UNPAYWALL_API = "https://api.unpaywall.org/v2"


def _first(dicts: Iterable[Optional[dict[str, Any]]], *keys: str) -> Optional[Any]:
    for d in dicts:
        if not d:
            continue
        for key in keys:
            value = d.get(key)
            if value:
                return value
    return None


def paper_from_crossref(item: dict[str, Any]) -> Paper:
    title = _first([item], "title", "container-title")
    if isinstance(title, list):
        title = title[0] if title else None
    title = clean_text(str(title)) if title else "Untitled"
    abstract = clean_text(item.get("abstract"))
    year = None
    issued = item.get("issued", {}).get("date-parts", [[None]])
    if issued and issued[0] and issued[0][0]:
        try:
            year = int(issued[0][0])
        except (TypeError, ValueError):
            year = None
    authors: list[str] = []
    for a in item.get("author", []) or []:
        name = " ".join(x for x in [a.get("given"), a.get("family")] if x)
        if name:
            authors.append(name)
    doi = item.get("DOI")
    links = item.get("link") or []
    pdf_url = None
    for link in links:
        if link.get("content-type") == "application/pdf" or str(link.get("URL", "")).endswith(".pdf"):
            pdf_url = link.get("URL")
            break
    url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
    return Paper(
        title=title,
        abstract=abstract,
        year=year,
        authors=authors,
        doi=doi,
        url=url,
        pdf_url=pdf_url,
        source="crossref",
        external_ids={"crossref": item.get("DOI", "")} if doi else {},
        raw={"crossref": item},
    )


def paper_from_semantic(item: dict[str, Any]) -> Paper:
    title = clean_text(item.get("title")) or "Untitled"
    abstract = clean_text(item.get("abstract"))
    year = item.get("year")
    try:
        year = int(year) if year is not None else None
    except (TypeError, ValueError):
        year = None
    authors = [a.get("name", "") for a in (item.get("authors") or []) if a.get("name")]
    external_ids = {k: str(v) for k, v in (item.get("externalIds") or {}).items() if v}
    paper_id = item.get("paperId")
    if paper_id:
        external_ids["SemanticScholar"] = paper_id
    oa = item.get("openAccessPdf") or {}
    pdf_url = oa.get("url") or None
    url = item.get("url") or None
    return Paper(
        title=title,
        abstract=abstract,
        year=year,
        authors=authors,
        doi=external_ids.get("DOI"),
        url=url,
        pdf_url=pdf_url,
        source="semantic_scholar",
        external_ids=external_ids,
        raw={"semantic_scholar": item},
    )


def paper_from_openalex(item: dict[str, Any]) -> Paper:
    title = clean_text(item.get("title")) or "Untitled"
    abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
    year = item.get("publication_year")
    try:
        year = int(year) if year is not None else None
    except (TypeError, ValueError):
        year = None
    authors = []
    for a in item.get("authorships") or []:
        name = ((a.get("author") or {}).get("display_name"))
        if name:
            authors.append(name)
    doi = item.get("doi")
    if doi:
        doi = doi.replace("https://doi.org/", "")
    oa = item.get("open_access") or {}
    pdf_url = oa.get("oa_url") or None
    url = item.get("doi") or item.get("id")
    ids = item.get("ids") or {}
    external_ids = {}
    if item.get("id"):
        external_ids["OpenAlex"] = str(item["id"])
    if doi:
        external_ids["DOI"] = doi
    if ids.get("mag"):
        external_ids["MAG"] = str(ids["mag"])
    return Paper(
        title=title,
        abstract=abstract,
        year=year,
        authors=authors,
        doi=doi,
        url=url,
        pdf_url=pdf_url,
        source="openalex",
        external_ids=external_ids,
        raw={"openalex": item},
    )


def paper_from_arxiv(entry: ET.Element) -> Paper:
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    title = clean_text(entry.findtext("atom:title", default="", namespaces=ns))
    summary = clean_text(entry.findtext("atom:summary", default="", namespaces=ns))
    authors = [a.findtext("atom:name", default="", namespaces=ns) for a in entry.findall("atom:author", ns)]
    authors = [a for a in authors if a]
    url = entry.findtext("atom:id", default="", namespaces=ns)
    arxiv_id = None
    if url:
        m = re.search(r"(?:abs|pdf)/([^/v]+)", url)
        if m:
            arxiv_id = m.group(1)
    year = None
    published = entry.findtext("atom:published", default="", namespaces=ns)
    if published:
        year = int(published[:4]) if len(published) >= 4 else None
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None
    external = {"arXiv": arxiv_id} if arxiv_id else {}
    return Paper(
        title=title,
        abstract=summary,
        year=year,
        authors=authors,
        url=url,
        pdf_url=pdf_url,
        arxiv_id=arxiv_id,
        source="arxiv",
        external_ids=external,
        raw={"arxiv": entry},
    )


def search_crossref(query: str, client: HTTPClient) -> list[Paper]:
    params = {
        "query.title": query,
        "rows": 3,
        "select": "DOI,title,author,issued,abstract,reference,link,URL,container-title",
    }
    resp = client.get(CROSSREF_API, params=params)
    items = resp.json().get("message", {}).get("items", []) if resp.content else []
    return [paper_from_crossref(item) for item in items]


def search_semantic(query: str, client: HTTPClient) -> list[Paper]:
    params = {
        "query": query,
        "limit": 3,
        "fields": "title,abstract,year,authors,externalIds,openAccessPdf,url,citationCount,referenceCount",
    }
    resp = client.get(f"{SEMANTIC_API}/paper/search", params=params)
    data = resp.json()
    items = data.get("data", []) if isinstance(data, dict) else []
    return [paper_from_semantic(item) for item in items]


def search_openalex(query: str, client: HTTPClient) -> list[Paper]:
    params = {
        "search": query,
        "per-page": 3,
        "select": "id,doi,title,publication_year,authorships,abstract_inverted_index,open_access,referenced_works,primary_location,ids",
    }
    resp = client.get(OPENALEX_API, params=params)
    items = resp.json().get("results", []) if resp.content else []
    return [paper_from_openalex(item) for item in items]


def search_arxiv(query: str, client: HTTPClient) -> list[Paper]:
    params = {
        "search_query": f'all:"{query}"',
        "start": 0,
        "max_results": 3,
    }
    resp = client.get(ARXIV_API, params=params)
    root = ET.fromstring(resp.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    return [paper_from_arxiv(entry) for entry in entries]


def _extract_doi(query: str) -> Optional[str]:
    """Return a DOI if the query looks like one or contains a doi.org link."""
    query = query.strip()
    m = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", query)
    if m:
        return m.group(0).rstrip(".,")
    if query.lower().startswith("doi:"):
        return query[4:].strip()
    return None


def _extract_arxiv_id(query: str) -> Optional[str]:
    query = query.strip()
    m = re.search(r"\d{4}\.\d{4,5}(?:v\d+)?", query)
    if m:
        return m.group(0)
    if query.lower().startswith("arxiv:"):
        return query.split(":", 1)[1].strip()
    return None


def fetch_crossref_by_doi(doi: str, client: HTTPClient) -> Paper:
    resp = client.get(f"{CROSSREF_API}/{urllib.parse.quote(doi, safe='')}")
    return paper_from_crossref(resp.json().get("message", {}))


def fetch_semantic_by_id(identifier: str, client: HTTPClient) -> Paper:
    fields = "title,abstract,year,authors,externalIds,openAccessPdf,url,citationCount"
    resp = client.get(f"{SEMANTIC_API}/paper/{urllib.parse.quote(identifier, safe='')}", params={"fields": fields})
    return paper_from_semantic(resp.json())


def fetch_arxiv_by_id(arxiv_id: str, client: HTTPClient) -> Paper:
    params = {"id_list": arxiv_id, "max_results": 1}
    resp = client.get(ARXIV_API, params=params)
    root = ET.fromstring(resp.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    if not entries:
        raise RuntimeError(f"arXiv ID not found: {arxiv_id}")
    return paper_from_arxiv(entries[0])


def search_paper(query: str, client: HTTPClient) -> Paper:
    """Search several sources and return the best candidate."""
    errors: list[str] = []
    candidates: list[Paper] = []

    # Direct identifiers are usually more reliable than a title search.
    doi = _extract_doi(query)
    arxiv_id = _extract_arxiv_id(query)
    if doi:
        try:
            return fetch_crossref_by_doi(doi, client)
        except Exception as exc:
            errors.append(f"crossref-doi: {exc}")
        try:
            return fetch_semantic_by_id(f"DOI:{doi}", client)
        except Exception as exc:
            errors.append(f"semantic-doi: {exc}")
    if arxiv_id:
        try:
            return fetch_arxiv_by_id(arxiv_id, client)
        except Exception as exc:
            errors.append(f"arxiv-id: {exc}")
        try:
            return fetch_semantic_by_id(f"ARXIV:{arxiv_id}", client)
        except Exception as exc:
            errors.append(f"semantic-arxiv: {exc}")

    for fn in (search_semantic, search_openalex, search_crossref, search_arxiv):
        try:
            found = fn(query, client)
            if found:
                candidates.extend(found)
        except Exception as exc:  # network/API errors
            errors.append(f"{fn.__name__}: {exc}")

    # Simple ranking: prefer papers with abstract, then PDF, then citation count from raw.
    def score(p: Paper) -> tuple[int, int]:
        # 标题完全匹配是最强的相关性信号。
        exact_score = 4 if p.title.strip().lower() == query.strip().lower() else 0
        abstract_score = 2 if p.abstract else 0
        pdf_score = 1 if p.pdf_url else 0
        # arXiv 记录几乎总是规范版本，且 PDF 一定可下载，优先选择。
        arxiv_score = 2 if p.arxiv_id else 0
        citations = 0
        raw = p.raw.get("semantic_scholar") or p.raw.get("openalex") or {}
        citations = int(raw.get("citationCount") or raw.get("cited_by_count") or 0)
        return (exact_score + abstract_score + pdf_score + arxiv_score, citations)

    if candidates:
        candidates.sort(key=score, reverse=True)
        best = candidates[0]
        # Try to merge DOI/PDF/abstract from other candidates with same DOI/title.
        best = _merge_candidates(best, candidates[1:])
        return best

    raise RuntimeError(
        "Could not find the paper from any source. "
        "Please check the title or use a DOI/arXiv ID. Details: "
        + "; ".join(errors)
    )


def _merge_candidates(primary: Paper, others: list[Paper]) -> Paper:
    primary.title = primary.title or "Untitled"
    for other in others:
        if other.title.lower() == primary.title.lower():
            if not primary.abstract and other.abstract:
                primary.abstract = other.abstract
            if not primary.pdf_url and other.pdf_url:
                primary.pdf_url = other.pdf_url
            if not primary.doi and other.doi:
                primary.doi = other.doi
                primary.external_ids["DOI"] = other.doi
            if not primary.arxiv_id and other.arxiv_id:
                primary.arxiv_id = other.arxiv_id
                primary.pdf_url = primary.pdf_url or other.pdf_url
            primary.external_ids.update(other.external_ids)
            if not primary.authors and other.authors:
                primary.authors = other.authors
    return primary


def _semantic_id_for(paper: Paper) -> Optional[str]:
    if paper.external_ids.get("SemanticScholar"):
        return paper.external_ids["SemanticScholar"]
    if paper.doi:
        return f"DOI:{paper.doi}"
    if paper.arxiv_id:
        return f"ARXIV:{paper.arxiv_id}"
    return None


def semantic_references(paper: Paper, client: HTTPClient, max_refs: int) -> list[Paper]:
    sid = _semantic_id_for(paper)
    if not sid:
        return []
    params = {
        "fields": "title,abstract,year,authors,externalIds,openAccessPdf,url,citationCount",
        "limit": max_refs,
    }
    resp = client.get(f"{SEMANTIC_API}/paper/{urllib.parse.quote(sid, safe='')}/references", params=params)
    data = resp.json()
    items = data.get("data", []) if isinstance(data, dict) else []
    refs = []
    for entry in items:
        cited = entry.get("citedPaper") or {}
        if cited.get("title"):
            refs.append(paper_from_semantic(cited))
    return refs


def _openalex_id_for(paper: Paper) -> Optional[str]:
    if paper.external_ids.get("OpenAlex"):
        return paper.external_ids["OpenAlex"]
    if paper.doi:
        return f"doi:{paper.doi}"
    return None


def openalex_references(paper: Paper, client: HTTPClient, max_refs: int) -> list[Paper]:
    oid = _openalex_id_for(paper)
    if not oid:
        return []
    fields = "id,doi,title,publication_year,authorships,abstract_inverted_index,open_access,ids"
    resp = client.get(f"{OPENALEX_API}/{urllib.parse.quote(oid, safe='')}", params={"select": "id,referenced_works"})
    data = resp.json() if resp.content else {}
    ref_ids = (data.get("referenced_works") or [])[:max_refs]
    refs = []
    for ref_id in ref_ids:
        try:
            r = client.get(f"{OPENALEX_API}/{urllib.parse.quote(ref_id, safe='')}", params={"select": fields})
            refs.append(paper_from_openalex(r.json()))
        except Exception:
            continue
    return refs


def crossref_references(paper: Paper, client: HTTPClient, max_refs: int) -> list[Paper]:
    raw_refs = (paper.raw.get("crossref") or {}).get("reference") or []
    refs = []
    for ref in raw_refs[:max_refs]:
        title = clean_text(ref.get("article-title") or ref.get("unstructured") or ref.get("key"))
        doi = ref.get("DOI")
        year = None
        try:
            year = int(ref.get("year")) if ref.get("year") else None
        except (TypeError, ValueError):
            year = None
        if not title and doi:
            title = f"Reference DOI {doi}"
        if not title:
            continue
        p = Paper(
            title=title or "Untitled",
            year=year,
            doi=doi,
            url=f"https://doi.org/{doi}" if doi else None,
            source="crossref_reference",
            external_ids={"DOI": doi} if doi else {},
        )
        refs.append(p)
    return refs


def references_for(paper: Paper, client: HTTPClient, max_refs: int) -> list[Paper]:
    """Return reference papers, enriched with abstract/PDF where possible."""
    # 1) Semantic Scholar references (richest metadata).
    try:
        refs = semantic_references(paper, client, max_refs)
        if refs:
            return refs
    except Exception:
        pass

    # 2) OpenAlex references.
    try:
        refs = openalex_references(paper, client, max_refs)
        if refs:
            return refs
    except Exception:
        pass

    # 3) Crossref reference list as a fallback.
    try:
        refs = crossref_references(paper, client, max_refs)
        return refs
    except Exception:
        return []


def resolve_pdf_url(paper: Paper, client: HTTPClient, unpaywall_email: Optional[str] = None) -> Optional[str]:
    """Try to find a direct PDF URL if not already known."""
    if paper.pdf_url:
        return paper.pdf_url
    if paper.arxiv_id:
        return f"https://arxiv.org/pdf/{paper.arxiv_id}"

    # Unpaywall can find OA PDFs from a DOI.
    if paper.doi and unpaywall_email:
        try:
            resp = client.get(
                f"{UNPAYWALL_API}/{urllib.parse.quote(paper.doi, safe='')}",
                params={"email": unpaywall_email},
            )
            data = resp.json()
            loc = data.get("best_oa_location") or {}
            pdf_url = loc.get("url_for_pdf") or loc.get("url")
            if pdf_url:
                return pdf_url
        except Exception:
            pass

    # Crossref link fallback.
    if paper.doi:
        try:
            resp = client.get(f"{CROSSREF_API}/{urllib.parse.quote(paper.doi, safe='')}",
                              params={"select": "link,URL"})
            item = resp.json().get("message", {})
            for link in item.get("link") or []:
                if link.get("content-type") == "application/pdf" or str(link.get("URL", "")).endswith(".pdf"):
                    return link.get("URL")
        except Exception:
            pass

    return None


def download_pdf(paper: Paper, dest, client: HTTPClient, unpaywall_email: Optional[str] = None) -> bool:
    """Download the paper PDF to dest. Returns True on success."""
    url = resolve_pdf_url(paper, client, unpaywall_email)
    if not url:
        return False
    try:
        resp = client.session.get(url, allow_redirects=True, timeout=client.timeout)
        resp.raise_for_status()
        # Always verify the body begins with the PDF magic bytes. Some servers
        # return an HTML page even when the URL/path looks like a PDF.
        content = resp.content
        if content[:5] != b"%PDF-":
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        return dest.stat().st_size > 0
    except Exception:
        return False
