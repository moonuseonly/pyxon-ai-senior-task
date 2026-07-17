# Pyxon AI Entry Task — Agentic Search + URL + RAG Swarm

A multi-agent system built with **LangGraph** (orchestration) and **LlamaIndex**
(RAG), backed entirely by free-tier / local tools: **Groq** (LLM), **Tavily**
+ **DuckDuckGo** (search), and a local **HuggingFace + Chroma** RAG layer.

It takes a user question, routes it through a supervisor, gathers external
data (web search and/or a specific URL) when needed, grounds the answer in
retrieved evidence, and returns a short, citation-free final answer.

---

## Features implemented

- [x] Agent with a search data source (Tavily, with a DuckDuckGo fallback) + LLM
- [x] Agent that fetches URLs/APIs and uses the content to answer
- [x] Agent swarm (LangGraph, 4 nodes: supervisor → research/direct → writer)
- [x] RAG integration (LlamaIndex + local embeddings + Chroma)
- [x] Small benchmark (3 fixed Q&A pairs, checks routing behavior)
- [x] Full end-to-end runnable example (`main.py`)
- [ ] Docker/K8s deployment notes (not included in this pass)

---

## Architecture

```
                        ┌──────────────────┐
        question   ───► │    Supervisor     │
                        │  URL in question?  │
                        │  → research         │
                        │  else ask the LLM   │
                        └─────────┬──────────┘
                    ┌─────────────┴─────────────┐
                    ▼                            ▼
          ┌──────────────────┐         ┌──────────────────┐
          │  Research Agent   │         │   Direct Answer    │
          │  tools:           │         │  (no tools, plain   │
          │   - web_search    │         │   LLM call)          │
          │   - fetch_url     │         └──────────┬───────────┘
          └─────────┬─────────┘                    │
                    ▼                                │
          ┌──────────────────┐                       │
          │   RAG (Chroma)     │                       │
          │  index findings →   │                       │
          │  retrieve top-3      │                       │
          └─────────┬─────────┘                       │
                    ▼                                │
          ┌──────────────────┐                       │
          │   Writer Agent      │                       │
          │  synthesizes final   │                       │
          │  grounded answer      │                       │
          └─────────┬─────────┘                       │
                    └───────────────┬───────────────────┘
                                    ▼
                              final_answer
```

**Division of labor:**
- **Supervisor** (`src/graph.py::supervisor_node`) — decides whether a question
  needs external data. If the question literally contains a URL, it always
  routes to research (a deterministic check — this isn't left to LLM judgment,
  see *Design decisions* below). Otherwise it asks the LLM to classify the
  question as needing research or not.
- **Research Agent** (`src/agent.py`) — a tool-using LangChain agent
  (`create_agent`) with two tools: `web_search` (Tavily, DuckDuckGo fallback)
  and `fetch_url` (GET requests + HTML/JSON parsing). It decides on its own
  which tool(s) to call and how many times.
- **RAG layer** (`src/rag.py`) — every research result gets chunked, embedded
  locally (`sentence-transformers/all-MiniLM-L6-v2`, no API key, no rate
  limit), and stored in a persistent Chroma collection. The top-3 most
  relevant chunks for the *specific question* are retrieved before the writer
  agent runs — this is the actual "retrieval before generation" step, and it
  means the final answer is grounded in indexed evidence rather than just
  whatever the research agent happened to say last.
- **Writer Agent** (`src/graph.py::writer_node`) — a separate, tools-free LLM
  call that reads only the retrieved findings and produces one short (1-3
  sentence), plain-prose answer. Splitting this out from the research agent
  keeps the final answer clean, since the research agent's own output can
  include tool-call reasoning traces.
- **Direct Answer** (`src/graph.py::direct_node`) — for questions that don't
  need external data (e.g. arithmetic), skips research/RAG entirely and
  answers straight from the LLM.

### Design decisions worth calling out

- **Model choice:** `openai/gpt-oss-120b` on Groq. Originally targeted
  `llama-3.3-70b-versatile`, but Groq deprecated it (June 2026) in favor of
  this model, which also has stronger tool-calling reliability.
- **URL routing is deterministic, not LLM-judged.** During testing, letting
  the supervisor's LLM call decide the route caused a real hallucination: for
  a question containing a GitHub API URL, the model decided it already "knew"
  the answer and skipped research — then fabricated a plausible-looking but
  fake JSON response (invented star counts, timestamps, IDs). Fix: if a
  question contains `http://` or `https://`, routing to research is forced,
  no LLM judgment involved. This is documented in `supervisor_node`.
- **Search fallback:** Tavily is tried first (cleaner, agent-optimized
  results); if it errors for any reason, the tool silently falls back to
  DuckDuckGo, which needs no API key at all.
- **Grounding constraint:** every agent's system prompt explicitly forbids
  guessing or filling in gaps beyond what tool/search results actually say —
  this is the main anti-hallucination guardrail, on top of the RAG retrieval
  step.

---

## How to run

### 1. Requirements
- Python 3.11+
- Free API keys (no credit card needed for either):
  - **Groq**: https://console.groq.com → API Keys
  - **Tavily**: https://tavily.com → Dashboard

### 2. Setup (Windows / PowerShell)

```powershell
python -m venv newenv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\newenv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(macOS/Linux: `python3 -m venv newenv && source newenv/bin/activate` instead
of the two PowerShell-specific lines.)

### 3. Add your API keys

```powershell
cp .env.example .env
```

Open `.env` and paste your real `GROQ_API_KEY` and `TAVILY_API_KEY`.

### 4. Run

**Run the benchmark** (3 fixed Q&A pairs, checks routing + prints answers):
```powershell
python main.py
```

**Ask a single question:**
```powershell
python main.py "What is the current weather in Riyadh?"
```

First run will be a little slower — it downloads the local embedding model
(~90MB, one-time only) and creates a `chroma_db/` folder for the vector
store (persists between runs).

---

## Example questions & expected behavior

| Question | Route | What happens |
|---|---|---|
| `What is 15% of 200?` | `direct` | Supervisor sees no URL and no need for external info → answers straight from the LLM, no tools called. |
| `What is the current weather in Riyadh?` | `research` | Supervisor routes to research → `web_search` called via Tavily/DuckDuckGo → results indexed in Chroma → retrieved → writer produces a short grounded answer. |
| `What does the API at https://api.github.com/repos/langchain-ai/langgraph return?` | `research` (forced) | URL detected → `fetch_url` called directly on the API → JSON parsed → writer describes the actual response fields, not a guessed/fabricated one. |

---

## Assumptions

- LLM: Groq's `openai/gpt-oss-120b` (free tier, no card required).
- Search: Tavily as primary provider (free tier, 1,000 calls/month), with
  DuckDuckGo (`duckduckgo-search`, no key) as an automatic fallback.
- Embeddings: local `sentence-transformers/all-MiniLM-L6-v2` via
  HuggingFace, chosen specifically to keep RAG indexing free and decoupled
  from the LLM's rate limit.
- Vector store: Chroma, persisted locally to `./chroma_db`.
- Content fetched via `fetch_url` is truncated to 1,500 characters to keep
  tool output focused and within reasonable context size.

---

## Project structure

```
pyxon-agent-swarm/
├── main.py                  # entry point: benchmark or single-question CLI
├── requirements.txt
├── .env.example
├── .gitignore
└── src/
    ├── config.py             # env vars, Groq LLM, embedding model setup
    ├── rag.py                 # Chroma indexing + retrieval
    ├── agent.py                # research_agent (web_search + fetch_url tools)
    ├── graph.py                 # SwarmState + supervisor/research/direct/writer nodes
    └── tools/
        ├── search_tool.py       # Tavily + DuckDuckGo fallback
        └── url_tool.py            # HTTP GET + HTML/JSON parsing
```

---

## Security notes

- No API keys are hardcoded anywhere in the code — both `GROQ_API_KEY` and
  `TAVILY_API_KEY` are loaded from environment variables via `.env`
  (git-ignored).
- `fetch_url` makes outbound GET requests to whatever URL it's given; this
  is scoped to read-only GET requests with a 10-second timeout, and content
  is truncated before being passed to the LLM.
