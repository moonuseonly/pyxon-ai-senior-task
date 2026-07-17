"""
URL/API fetch tool: retrieves a specific URL and returns its content,
handling both HTML pages and JSON API responses.
"""
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


@tool
def fetch_url(url: str) -> str:
    """
    Fetch the content of a specific URL — a webpage or a JSON API endpoint.
    Use this when the user gives you an exact URL and asks you to read,
    summarize, or explain what it contains or returns.

    Args:
        url: The full URL to fetch, including https://
    """
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

    content_type = response.headers.get("Content-Type", "")

    if "application/json" in content_type:
        return f"JSON response from {url}:\n{response.text[:1500]}"

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())

    return f"Page content from {url}:\n{text[:1500]}"
