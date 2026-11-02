# =============================================================================
# app/api/routes.py: the HTTP API that the browser UI talks to
# -----------------------------------------------------------------------------
#   GET  /api/health  -> "is the server up?" check (used by monitors/Docker)
#   POST /api/chat    -> ask a question; runs the LangGraph agent
#   POST /api/ingest  -> upload a new company document (admin key required)
#
# Interactive docs for these endpoints: http://127.0.0.1:8080/docs
# =============================================================================
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.rag.workflow import ask
from app.rag.vectorstore import add_documents
from app.services.ingestion import load_file, chunk_documents, SUPPORTED
from app.services.audit import write_audit

# Every route below is mounted under the /api prefix.
router = APIRouter(prefix="/api")
settings = get_settings()

# Shape of the JSON body for /api/chat, e.g. {"question": "How do I reset my password?"}.
# FastAPI validates it automatically: 2 to 3000 characters, otherwise HTTP 422.
class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@router.post("/chat")
def chat(payload: ChatRequest):
    try:
        # Run the whole agent (route -> retrieve -> grade -> ... -> answer).
        result = ask(payload.question)
        # Log the question and the path the agent took to SQLite.
        write_audit(payload.question, result["source_used"], result.get("trace", []))

        # What the UI receives and displays.
        return {
            "answer": result["answer"],                 # the final text answer
            "source_used": result["source_used"],       # private_kb / web_search / direct / insufficient_evidence
            "trace": result.get("trace", []),           # step-by-step decision log
            "citations": result.get("citations", []),   # file names or web links
            "rewritten_query": result.get("current_query", payload.question),  # query after any rewrite

        }

    except Exception as exc:
        # Any failure (missing API key, provider outage, ...) becomes HTTP 500
        # with the error message, which the UI shows to the user.
        raise HTTPException(status_code=500, detail=str(exc)) from exc



@router.post("/ingest")
async def ingest(file: UploadFile = File(...), x_admin_key: str = Header(default="")):
    # 1. Security: the request must carry header "X-Admin-Key" matching ADMIN_API_KEY.
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    # 2. Validation: only PDF / TXT / MD / DOCX are accepted.
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Supported: {', '.join(sorted(SUPPORTED))}")
    # 3. Save the file into uploads/. Path(...).name strips any folder parts
    #    from the filename so an upload cannot write outside that folder.
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / Path(file.filename).name
    dest.write_bytes(await file.read())
    # 4. Same pipeline as ingest_sample_kb.py: load -> chunk -> embed + store in Pinecone.
    docs = load_file(dest)
    chunks = chunk_documents(docs)
    ids = add_documents(chunks)
    # The new document is searchable immediately.
    return {"message": "Document indexed", "file": dest.name, "chunks": len(chunks), "ids_created": len(ids)}
