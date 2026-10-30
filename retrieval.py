"""Semantic Scholar abstract retrieval; no claim of full OSDS coverage."""

def search(query, key="", year="", limit=10, session=None):
    if session is None:
        import requests
        session = requests
    params = {"query": query, "limit": min(max(limit, 1), 30),
              "fields": "title,abstract,url,year,citationCount,authors"}
    if year.strip():
        params["year"] = year.strip()
    response = session.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params=params, headers={"x-api-key": key} if key else {}, timeout=45)
    response.raise_for_status()
    papers = response.json().get("data", [])
    contexts, seen = [], set()
    for paper in papers:
        if not paper.get("abstract") or not paper.get("title"):
            continue
        identity = paper.get("paperId") or paper["title"]
        if identity in seen:
            continue
        seen.add(identity)
        contexts.append({
            "title": paper["title"], "text": paper["abstract"],
            "abstract": paper["abstract"], "url": paper.get("url", ""),
            "year": paper.get("year"), "citation_counts": paper.get("citationCount") or 0})
    return contexts

def search_europe_pmc(query, year="", limit=10, session=None):
    """Public biomedical/life-science abstracts, explicitly selected by user."""
    if session is None:
        import requests
        session = requests
    if year.strip():
        import re
        if not re.fullmatch(r"\d{4}(-\d{4})?", year.strip()):
            raise ValueError("年份请使用 YYYY 或 YYYY-YYYY。")
        years = year.strip().split("-")
        query = f"({query}) AND FIRST_PDATE:[{years[0]}-01-01 TO {years[-1]}-12-31]"
    response = session.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                           params={"query": query, "format": "json", "resultType": "core",
                                   "pageSize": min(max(limit, 1), 30)}, timeout=45)
    response.raise_for_status()
    from html import unescape
    import re
    results, seen = [], set()
    for paper in response.json().get("resultList", {}).get("result", []):
        identity = (paper.get("source"), paper.get("id"))
        abstract = unescape(re.sub(r"<[^>]+>", " ", paper.get("abstractText") or ""))
        if not abstract.strip() or not paper.get("title") or identity in seen:
            continue
        seen.add(identity)
        results.append({"title": paper["title"], "text": abstract,
                        "abstract": abstract, "year": paper.get("pubYear"),
                        "url": f"https://europepmc.org/article/{identity[0]}/{identity[1]}",
                        "citation_counts": int(paper.get("citedByCount") or 0),
                        "source": "Europe PMC"})
    return results

def search_osds(query, endpoint, year="", limit=50, session=None):
    """Adapt official PES2O search response; requires a real hosted index."""
    if not endpoint.strip():
        raise ValueError("尚未配置 OSDS_SEARCH_URL，请先部署 OSDS 检索服务。")
    if year.strip():
        raise ValueError("当前 OSDS 适配器不支持年份筛选，请清空年份。")
    if session is None:
        import requests
        session = requests
    response = session.post(endpoint, json={"query": query, "domains": "pes2o", "n_docs": limit}, timeout=120)
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results", {})
    if "documents" in payload:
        contexts = []
        for item in payload["documents"]:
            if item.get("text"):
                contexts.append({"title": item.get("title") or "OSDS 段落（标题未提供）",
                                 "text": item["text"], "url": item.get("url") or "",
                                 "year": item.get("year"), "citation_counts": item.get("citation_counts") or 0,
                                 "source": "OSDS"})
        return contexts[:limit]
    passages, ids = results.get("passages"), results.get("pes2o IDs")
    if not isinstance(passages, list) or not isinstance(ids, list) or len(passages) != len(ids):
        raise ValueError("OSDS 服务响应格式不匹配，需要 passages 与 pes2o IDs 列表。")
    return [{"title": f"OSDS 段落 · CorpusID {pid}（标题待补充）", "text": passage,
             "url": "", "year": None, "corpus_id": str(pid), "citation_counts": 0,
             "source": "OSDS"} for passage, pid in zip(passages, ids) if isinstance(passage, str) and passage.strip()][:limit]
