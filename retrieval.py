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
