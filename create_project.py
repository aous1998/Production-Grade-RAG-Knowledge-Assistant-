# =============================================================================
# create_project.py: one-off scaffolding helper (not needed to run the app)
# -----------------------------------------------------------------------------
# Creates the empty folder and file layout this project started from.
# Safe to re-run: existing folders and files are left untouched.
# =============================================================================
from pathlib import Path

# Current working directory
root = Path(".")

# Folders to create

folders = [
    "app/api",
    "app/core",
    "app/rag",
    "app/services",
    "data",
    "templates",
    "static",
    "uploads",
    "tests",
]



# Files to create
files = [
    "app/main.py",
    "ingest_sample_kb.py",
    "requirements.txt",
    "run.py",
    ".env",
]


# Create folders (parents=True builds nested paths; exist_ok=True skips existing ones)
for folder in folders:
    (root / folder).mkdir(parents=True, exist_ok=True)


# Create empty files (exist_ok=True never overwrites an existing file)
for file in files:
    (root / file).touch(exist_ok=True)



print("Project structure created successfully.")
