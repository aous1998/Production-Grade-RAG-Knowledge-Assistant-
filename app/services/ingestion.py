# =============================================================================
# app/services/ingestion.py: read documents and cut them into chunks
# -----------------------------------------------------------------------------
# Used by ingest_sample_kb.py and by the /api/ingest upload endpoint.
#
# Why chunk? An LLM answers best from short, focused passages. Searching small
# chunks lets Pinecone return just the relevant paragraph about, say, VPN
# setup, instead of a whole 20-page handbook.
# =============================================================================
from pathlib import Path
from typing import Iterable
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from docx import Document as DocxDocument


# File types the app accepts. The upload endpoint rejects anything else.
SUPPORTED = {".pdf", ".txt", ".md", ".docx"}



def load_file(path: Path) -> list[Document]:
    """Read one file and return LangChain Documents (text + metadata such as "source")."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        # One Document per PDF page; metadata includes the page number.
        return PyPDFLoader(str(path)).load()
    if suffix in {".txt", ".md"}:
        # Plain text and Markdown are read as one Document.
        return TextLoader(str(path), encoding="utf-8").load()
    if suffix == ".docx":
        # Word files: join all non-empty paragraphs into one Document.
        # "source" metadata is set manually so citations show the file name.
        doc = DocxDocument(str(path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [Document(page_content=text, metadata={"source": str(path)})]
    raise ValueError(f"Unsupported file type: {suffix}")



def chunk_documents(docs: Iterable[Document]) -> list[Document]:
    """Split Documents into ~900-character chunks that overlap by 120 characters.

    The splitter prefers to break at paragraphs, then lines, then sentences, so
    chunks stay readable. The overlap keeps a sentence that crosses a chunk
    boundary present in both neighbours. add_start_index records where each
    chunk began in the original text.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120, add_start_index=True)
    return splitter.split_documents(list(docs))
