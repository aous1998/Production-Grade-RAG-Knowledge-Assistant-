# =============================================================================
# app/core/logging.py: one shared log format for the whole app
# -----------------------------------------------------------------------------
# Called once at startup (from app/main.py). After this, any module that does
# `logging.getLogger(__name__).info(...)` prints a line like:
#   2026-11-02 10:15:01 | INFO | app.rag.workflow | message text
# =============================================================================
import logging

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,  # show INFO and above (INFO, WARNING, ERROR)
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
