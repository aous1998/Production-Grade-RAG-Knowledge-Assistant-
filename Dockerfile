# =============================================================================
# Dockerfile: package the app into a container image
# -----------------------------------------------------------------------------
# Build:  docker build -t rag-assistant .
# Run:    docker run --env-file .env -p 8080:8080 rag-assistant
# Then open http://localhost:8080
# (.env is excluded from the image by .dockerignore, so keys are passed at run time.)
# =============================================================================

# Small official Python base image.
FROM python:3.11-slim

# All following commands run inside /app in the container.
WORKDIR /app

# Don't write .pyc files; print logs immediately; default port.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Copy requirements first so Docker can cache the (slow) install step
# and reuse it when only the application code changes.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project.
COPY . .

EXPOSE 8080

# Start the web server, listening on all interfaces so the host can reach it.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
