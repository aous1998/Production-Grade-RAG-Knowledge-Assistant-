# =============================================================================
# ingest_sample_kb.py: load the demo company documents into Pinecone
# -----------------------------------------------------------------------------
# Run once before using the app:  python ingest_sample_kb.py
#
# Pipeline (the "LEARN" part of the project):
#   files in data/sample_kb/  ->  load text  ->  split into chunks
#   ->  turn each chunk into a vector (embedding)  ->  store in Pinecone
#
# After this, the agent can find these documents when employees ask questions.
# Running it again adds the chunks again (duplicates), so run it once per index.
# =============================================================================
from pathlib import Path
from app.core.config import get_settings
from app.services.ingestion import load_file, chunk_documents
from app.rag.vectorstore import add_documents

settings = get_settings()

# Every file in data/sample_kb (the IT handbook and the service desk runbook).
folder = Path(settings.sample_kb_dir)
files = [p for p in folder.iterdir() if p.is_file()]

# 1. Load: read each file into LangChain Document objects (text + metadata).
all_docs = []

for path in files:
    all_docs.extend(load_file(path))
# 2. Chunk: split long documents into small overlapping pieces for precise search.
chunks = chunk_documents(all_docs)
# 3. Embed + store: vectorise every chunk and upload it to Pinecone.
ids = add_documents(chunks)
print(f"Indexed {len(files)} files -> {len(chunks)} chunks -> {len(ids)} Pinecone vectors")
