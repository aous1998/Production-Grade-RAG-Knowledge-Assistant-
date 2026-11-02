# =============================================================================
# app/services/audit.py: record every question in a small SQLite database
# -----------------------------------------------------------------------------
# Enterprises need to know what was asked and how the AI reached its answer
# (debugging, compliance, finding gaps in the knowledge base). Every /api/chat
# call stores: time, question, which source answered, and the full agent trace.
#
# The database is a single file (data/audit.db) created automatically; it is
# git-ignored. Open it with any SQLite viewer, e.g. "DB Browser for SQLite".
# =============================================================================
import json
import sqlite3
from datetime import datetime, timezone
from app.core.config import get_settings

settings = get_settings()

def init_db() -> None:
    """Create the query_audit table if it does not exist yet (called at startup)."""
    con = sqlite3.connect(settings.audit_db_path)
    con.execute(
        """CREATE TABLE IF NOT EXISTS query_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            question TEXT NOT NULL,
            source_used TEXT NOT NULL,
            trace_json TEXT NOT NULL
        )"""
    )
    con.commit()
    con.close()

def write_audit(question: str, source_used: str, trace: list[str]) -> None:
    """Insert one row per answered question. The trace list is stored as JSON text."""
    con = sqlite3.connect(settings.audit_db_path)
    # "?" placeholders let SQLite insert the values safely (prevents SQL injection).
    con.execute(
        "INSERT INTO query_audit(created_at, question, source_used, trace_json) VALUES (?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), question, source_used, json.dumps(trace)),
    )
    con.commit()
    con.close()
