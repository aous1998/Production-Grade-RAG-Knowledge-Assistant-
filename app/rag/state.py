# =============================================================================
# app/rag/state.py: the data the agent carries between steps
# -----------------------------------------------------------------------------
# LangGraph passes one shared "state" dictionary from node to node. Each node
# (route, retrieve, grade, ...) reads what it needs and returns only the keys
# it changed; LangGraph merges those updates into the state.
#
# The two small Pydantic models force the LLM to answer router/grader
# questions in a fixed JSON shape, so the code can branch on them reliably.
# =============================================================================
from typing import List, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.documents import Document

# Router output: {"route": "kb"} for IT questions, {"route": "direct"} for chit-chat.
class RouteDecision(BaseModel):
    route: Literal["kb", "direct"] = Field(description="kb for IT/support questions; direct for greetings/simple chat")

# Grader output: {"grade": "good"} if the evidence can answer the question, else "weak".
class EvidenceGrade(BaseModel):
    grade: Literal["good", "weak"] = Field(description="Whether evidence is sufficient to answer")

class AgentState(TypedDict):
    question: str             # the employee's original question (never changes)
    current_query: str        # query used for searching; may be rewritten on retry
    kb_docs: List[Document]   # chunks returned by Pinecone
    web_results: str          # Tavily results flattened into one text block
    kb_grade: str             # "good" / "weak" verdict on kb_docs
    web_grade: str            # "good" / "weak" verdict on web_results
    answer: str               # final answer shown to the user
    source_used: str          # which path produced the answer (shown in the UI)
    retry_count: int          # how many query rewrites have happened
    trace: List[str]          # human-readable log of every step taken
    citations: List[dict]     # sources: {"title", "url", "type"}
