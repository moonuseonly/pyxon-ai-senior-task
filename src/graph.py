"""
The swarm: a supervisor routes each question to either the research agent
(search/fetch + RAG retrieval) or straight to a direct answer, then a
writer agent produces the final grounded response.
"""
from typing import TypedDict
from langgraph.graph import StateGraph, END

from src.config import llm
from src.agent import research_agent
from src.rag import index_findings, retrieve_relevant_chunks


class SwarmState(TypedDict):
    question: str
    route: str
    research_findings: str
    final_answer: str


def supervisor_node(state: SwarmState) -> dict:
    question = state["question"]

    # Deterministic check: a URL in the question always needs research —
    # no LLM judgment call needed for something this checkable. (This fixes
    # a real hallucination we hit during testing: the LLM once "answered"
    # a GitHub API question from memory instead of fetching it.)
    if "http://" in question or "https://" in question:
        return {"route": "research"}

    decision_prompt = (
        f"Question: {question}\n\n"
        "Does answering this question require searching the web for current/"
        "external information? Reply with exactly one word: 'research' if yes, "
        "'direct' if you can answer from general knowledge alone."
    )
    response = llm.invoke(decision_prompt)
    decision = response.content.strip().lower()
    return {"route": "research" if "research" in decision else "direct"}


def research_node(state: SwarmState) -> dict:
    response = research_agent.invoke({"messages": [{"role": "user", "content": state["question"]}]})
    findings = response["messages"][-1].content

    # Index raw findings, then retrieve back only what's relevant to this
    # question — this is the actual "retrieval before generation" step.
    index_findings(findings, state["question"])
    retrieved = retrieve_relevant_chunks(state["question"])

    return {"research_findings": retrieved if retrieved else findings}


def direct_node(state: SwarmState) -> dict:
    response = llm.invoke(state["question"])
    return {"final_answer": response.content}


def writer_node(state: SwarmState) -> dict:
    prompt = (
        f"Question: {state['question']}\n\n"
        f"Research findings:\n{state['research_findings']}\n\n"
        "Write a final answer to the question using only the findings above. "
        "1-3 sentences, plain prose, no citation markers."
    )
    response = llm.invoke(prompt)
    return {"final_answer": response.content}


graph_builder = StateGraph(SwarmState)
graph_builder.add_node("supervisor", supervisor_node)
graph_builder.add_node("research", research_node)
graph_builder.add_node("direct", direct_node)
graph_builder.add_node("writer", writer_node)

graph_builder.set_entry_point("supervisor")
graph_builder.add_conditional_edges(
    "supervisor",
    lambda state: state["route"],
    {"research": "research", "direct": "direct"},
)
graph_builder.add_edge("research", "writer")
graph_builder.add_edge("direct", END)
graph_builder.add_edge("writer", END)

swarm = graph_builder.compile()
