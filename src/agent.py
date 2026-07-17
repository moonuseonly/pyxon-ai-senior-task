"""
Research agent: a tool-using agent that can search the web and fetch URLs.
This is the "Research Agent" role in the swarm.
"""
from langchain.agents import create_agent

from src.config import llm
from src.tools.search_tool import web_search
from src.tools.url_fetch_tool import fetch_url

research_agent = create_agent(
    llm,
    tools=[web_search, fetch_url],
    system_prompt=(
        "You answer questions using web_search for general/current information, "
        "and fetch_url when the user gives a specific URL. Keep answers to 1-3 "
        "sentences. Only state facts that appear in the tool results — never "
        "guess or fill in gaps. Write in plain prose with no citation markers "
        "or bracketed references."
    ),
)
