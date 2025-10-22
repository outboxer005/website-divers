## AI-Based Data Acquisition Agent

A Python crawler that discovers and downloads datasets from a landing URL up to a configurable depth, capturing metadata and optionally using an AI reasoner to prioritize pages.

### Features
- Configurable crawl depth and concurrency
- Detects and downloads data files (.csv, .xlsx, .json, .zip, .pdf, etc.)
- Captures metadata (url, file_name, depth, content_type, file_size_kb, ai_score, timestamp)
- Optional AI reasoner (OpenAI) to prioritize data-rich pages
- CLI with Typer + Rich
- Web UI with FastAPI + Jinja templates

### Setup
1. Create venv and install deps
```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

2. (Optional) Configure environment variables
- `DB_URL` (defaults to local SQLite file `acquisition.db`)
- `OPENAI_API_KEY` (if using AI)

### CLI Usage
```bash
python -m main.cli crawl --url https://data.gov/ --depth 2 --concurrency 8 --output downloads
```

### Web UI Usage
Start the server:
```bash
uvicorn main.web:app --reload --port 8000
```
Open `http://localhost:8000` in your browser. Paste a landing URL, choose depth/concurrency, optionally enable AI, and click Start Crawl. The table shows recent downloaded files.

### Notes
- If using Postgres, ensure the database exists and `DB_URL` is set.
- Downloads are stored under `downloads/` by default.

