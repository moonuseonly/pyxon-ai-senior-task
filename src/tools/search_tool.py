"""
Search tool: Tavily (free tier, agent-optimized) as primary,
falling back to DuckDuckGo (no key needed) if Tavily fails.
"""
from langchain_core.tools import tool
from tavily import TavilyClient
from duckduckgo_search import DDGS

from src.config import TAVILY_API_KEY

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def web_search(query: str) -> str:
    """
    Searches the web for current and accurate information.
    Always prefer searching over guessing whenever the answer depends
    on recent information or there is uncertainty.

    Search query rules:
    - Use only the essential keywords.
    - Keep queries under 10 words when possible.
    - Include names, dates, locations, product versions, or organizations if relevant.
    - Never send the full user prompt.
    - If needed, perform multiple focused searches instead of one broad query.

    Avoid searching for:
    - Basic programming knowledge
    - General mathematics
    - Language translation
    - Logical reasoning
    - Information that is stable and unlikely to change

    Returns relevant web information that should be used to formulate an accurate answer.
    """
    try:
        response = tavily_client.search(query=query, max_results=5, include_answer=True)
        results = response.get("results", [])
    except Exception:
        results = []

    if not results:
        # NOTE: original version had `with DDGS as ddgs:` (missing parens) —
        # DDGS is a class, not an instance, so that would crash the moment
        # this fallback path ever actually ran. Fixed here.
        with DDGS() as ddgs:
            results = [
                {"title": r.get("title", ""), "url": r.get("href", ""), "content": r.get("body", "")}
                for r in ddgs.text(query, max_results=5)
            ]

    if not results:
        return f"No results found for: {query}"

    return "\n\n".join(
        f"[{i + 1}] {r['title']}\nURL: {r['url']}\n{r['content']}"
        for i, r in enumerate(results)
    )
