# =============================================================================
# app/rag/vectorstore.py: embeddings + Pinecone (the "memory" of the agent)
# -----------------------------------------------------------------------------
# Embeddings turn text into a list of numbers (a vector) so that texts with
# similar MEANING get similar vectors. "How do I log in remotely?" lands near
# the VPN instructions even though the words differ.
#
# Pinecone stores those vectors and, given a question's vector, returns the
# closest chunks (similarity search). This file:
#   - creates the embedding model (local HuggingFace or OpenAI),
#   - makes sure the Pinecone index exists with the right vector size,
#   - exposes helpers to search (get_retriever) and to add chunks (add_documents).
# =============================================================================
import time
from pinecone import Pinecone , ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.core.config import get_settings

settings = get_settings()


# Created lazily on first use and then reused (loading models is slow).
_embeddings = None
_vectorstore = None


# How many numbers each embedding model produces. A Pinecone index has a fixed
# vector size, so it must match the embedding model exactly.
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "all-minilm-l6-v2": 384,
    "sentence-transformers/all-minilm-l6-v2": 384,
}



def get_embedding_dimension(model_name: str | None = None) -> int:
    """Return the vector size for the configured embedding model."""
    name = (model_name or settings.embedding_model or "").strip()
    if not name:
        raise RuntimeError("Embedding model is not configured")

    # Exact match first, then a looser "contains" match (e.g. versioned names).
    normalized = name.lower()
    if normalized in EMBEDDING_DIMENSIONS:
        return EMBEDDING_DIMENSIONS[normalized]
    if "text-embedding-3-small" in normalized:
        return 1536
    if "text-embedding-3-large" in normalized:
        return 3072
    if "text-embedding-ada-002" in normalized:
        return 1536
    if "all-minilm" in normalized:
        return 384

    raise ValueError(
        f"Unsupported embedding model '{model_name or settings.embedding_model}' for Pinecone. "
        "Add the matching dimension to EMBEDDING_DIMENSIONS."
    )



def get_embeddings():
    """Return the embedding model (built once, then cached)."""
    global _embeddings
    if _embeddings is None:
        if settings.embedding_provider == "huggingface":
            # Free and local: downloads ~90 MB the first time, then works offline.
            # Imported here so the package is only needed when this provider is used.
            from langchain_huggingface import HuggingFaceEmbeddings
            _embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        else:
            # Paid OpenAI embeddings API.
            if not settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is missing")
            _embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=settings.openai_api_key,
            )
    return _embeddings




def ensure_index():
    """Make sure the Pinecone index exists and matches the embedding size.

    - Index missing          -> create it.
    - Index has wrong size   -> DELETE it and create a new one (this happens
                                after switching embedding models; you must
                                re-run ingest_sample_kb.py afterwards).
    """
    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is missing")

    desired_dimension = get_embedding_dimension()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    names = [x["name"] for x in pc.list_indexes()]

    if settings.pinecone_index_name in names:
        # Read the existing index's vector size (attribute or dict, depending on SDK version).
        index_info = pc.describe_index(settings.pinecone_index_name)
        current_dimension = getattr(index_info, "dimension", None)
        if current_dimension is None and isinstance(index_info, dict):
            current_dimension = index_info.get("dimension")

        if current_dimension is not None and current_dimension != desired_dimension:
            # Size mismatch: delete and wait until Pinecone confirms it is gone.
            pc.delete_index(name=settings.pinecone_index_name)
            while settings.pinecone_index_name in [x["name"] for x in pc.list_indexes()]:
                time.sleep(1)

    if settings.pinecone_index_name not in [x["name"] for x in pc.list_indexes()]:
        # Serverless index on AWS us-east-1 (available on Pinecone's free plan).
        # "cosine" = compare vectors by the angle between them (standard for text).
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=desired_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        # Wait until the new index is ready to accept data.
        while not pc.describe_index(settings.pinecone_index_name).status["ready"]:
            time.sleep(1)

    return pc.Index(settings.pinecone_index_name)





def get_vectorstore():
    """LangChain wrapper that combines the Pinecone index with the embedding model."""
    global _vectorstore
    if _vectorstore is None:
        index = ensure_index()
        _vectorstore = PineconeVectorStore(
            index=index,
            embedding=get_embeddings(),
            namespace=settings.pinecone_namespace,
        )
    return _vectorstore



def get_retriever():
    """Search helper used by the agent: returns the top_k most similar chunks."""
    return get_vectorstore().as_retriever(search_kwargs={"k": settings.top_k})



def add_documents(chunks):
    """Embed the chunks and upload them to Pinecone. Returns the new vector IDs."""
    store = get_vectorstore()
    return store.add_documents(chunks)
