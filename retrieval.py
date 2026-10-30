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
