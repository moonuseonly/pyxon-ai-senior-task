"""
RAG layer: persists research findings into a local Chroma vector store,
then retrieves only the most relevant chunks for a given query.
"""
import chromadb
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore

chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("research_findings")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)


def index_findings(text: str, question: str) -> None:
    doc = Document(text=text, metadata={"question": question})
    VectorStoreIndex.from_documents([doc], storage_context=storage_context)


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> str:
    index = VectorStoreIndex.from_vector_store(vector_store)
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    if not nodes:
        return ""
    return "\n\n".join(node.get_content() for node in nodes)
