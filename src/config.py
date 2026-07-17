"""
Central config: loads environment variables, exposes the shared Groq LLM,
and configures the local embedding model used by the RAG layer.
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY is not set. Copy .env.example to .env and add your key.")

# openai/gpt-oss-120b: Groq's current free-tier flagship model, chosen for
# reliable tool-calling (llama-3.3-70b-versatile was deprecated June 2026).
DEFAULT_MODEL = "openai/gpt-oss-120b"

llm = ChatGroq(model=DEFAULT_MODEL, temperature=0, api_key=GROQ_API_KEY)

# Local HuggingFace embedding model for RAG — free, no API key, no rate limit.
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
