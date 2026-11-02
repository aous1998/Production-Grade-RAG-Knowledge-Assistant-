# =============================================================================
# run.py: start the app locally with `python run.py`
# -----------------------------------------------------------------------------
# Launches the uvicorn web server, which runs the FastAPI app defined in
# app/main.py. Open http://127.0.0.1:8080 in a browser once it is running.
#   reload=True -> the server restarts automatically when you edit code
#                  (handy in development; the Dockerfile runs without it).
# Stop the server with Ctrl+C.
# =============================================================================
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
