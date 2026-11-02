# =============================================================================
# app/main.py: creates the FastAPI web application
# -----------------------------------------------------------------------------
# This is the "front door" of the backend. It:
#   1. sets up logging and the SQLite audit table,
#   2. plugs in the API routes (/api/chat, /api/ingest, /api/health),
#   3. serves the browser UI (templates/index.html + static CSS/JS).
#
# Started by `python run.py` (local) or by uvicorn inside Docker:
#   uvicorn app.main:app   ->  "the `app` object inside app/main.py"
# =============================================================================
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import router
from app.core.config import get_settings, BASE_DIR
from app.core.logging import configure_logging
from app.services.audit import init_db


# ---- One-time startup work (runs when this module is imported) --------------
configure_logging()       # consistent log format everywhere
settings = get_settings()  # load .env values
init_db()                 # make sure the SQLite audit table exists


# The web application object that uvicorn runs.
app = FastAPI(title=settings.app_name, version="1.0.0")

# Add the JSON API endpoints defined in app/api/routes.py (all under /api).
app.include_router(router)
# Serve files in /static (style.css, app.js) at the URL path /static/...
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
# Jinja2 renders HTML templates and can insert variables like {{ app_name }}.
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# GET / -> the chat page the employee sees in the browser.
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.app_name})
