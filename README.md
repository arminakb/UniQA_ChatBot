# IAU QA Chatbot

LLM-powered question-answering chatbot for Islamic Azad University, Sari Branch academic regulations. The project ingests Persian regulation documents, builds an Obsidian-compatible knowledge wiki, retrieves relevant pages, and serves answers through a FastAPI web interface.

## Features

- Persian academic regulation ingestion from PDF and Markdown sources.
- LLM-Wiki style Markdown knowledge base with source citations.
- Retrieval-backed chatbot with source snippets in responses.
- FastAPI JSON API and built-in browser UI.
- Runtime LLM key and base URL update endpoint for local demos.
- Offline-friendly test path with lexical retrieval fallback.

## Technologies

- Python 3.11+
- FastAPI and Uvicorn
- Pydantic
- Loguru
- LangGraph, optional with sequential fallback
- pdfplumber and PyMuPDF for PDF extraction
- ChromaDB and sentence-transformers as optional retrieval accelerators

## Project Structure

```text
.
├── iau_chatbot/              # Python package
│   ├── agent/                # Retrieval + answer generation graph
│   ├── api/                  # FastAPI app, schemas, services, UI
│   │   └── static/           # UI images served by the API
│   ├── ingest/               # PDF extraction and text segmentation
│   ├── retrieval/            # Metadata, lexical, and optional vector retrieval
│   └── wiki/                 # Wiki page schema, rendering, and storage
├── docs/                     # Ingestion and knowledge-base documentation
├── raw/                      # Source regulation files
├── wiki/                     # Generated/curated Markdown knowledge base
├── tests/                    # Automated tests
├── .env.example              # Safe environment template
├── pyproject.toml            # Package metadata and optional dependency groups
└── requirements.txt          # Convenience dependency list
```

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install from `pyproject.toml` with all runtime extras:

```bash
python -m pip install -e ".[all]"
```

For development and tests:

```bash
python -m pip install -e ".[all,dev]"
```

Alternatively, install the convenience dependency list:

```bash
python -m pip install -r requirements.txt
```

## Environment Variables

Create a local environment file from the template:

```bash
cp .env.example .env
```

Required:

- `LLM_API_KEY`: API key for the configured OpenAI-compatible LLM provider.

Common configuration:

- `BASE_URL`: OpenAI-compatible API base URL. Used when `LLM_BASE_URL` is not set.
- `LLM_BASE_URL`: Optional explicit LLM base URL override.
- `LLM_MODEL`: Chat model name.
- `EMBED_MODEL`: Embedding model name for optional vector retrieval.
- `PDF_DIR`: Source document directory.
- `WIKI_DIR`: Markdown wiki directory used by retrieval.
- `VECTOR_DB_PATH`: Local vector database path.
- `LOG_LEVEL`: Application log level.
- `FEEDBACK_PATH`: JSONL file for user feedback.
- `CHATBOT_TIMEOUT_SECONDS`: Per-request chatbot timeout.

Never commit `.env`, API keys, credentials, local vector stores, logs, or feedback files.

## Run The Project

Validate configuration:

```bash
python -m iau_chatbot --env-file .env
```

Preview PDF ingestion:

```bash
python -m iau_chatbot.ingest --env-file .env --dry-run
```

Build the wiki with the configured LLM:

```bash
python -m iau_chatbot.build_wiki --env-file .env
```

Run an offline deterministic wiki build for smoke testing:

```bash
python -m iau_chatbot.build_wiki --env-file .env --fake-llm
```

Start the API and web UI:

```bash
python -m iau_chatbot.api --env-file .env --host 127.0.0.1 --port 8000
```

Open the browser UI:

```text
http://127.0.0.1:8000/
```

## API Usage

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Ask a question:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"سقف واحد مجاز در هر ترم چقدر است؟","session_id":"demo"}'
```

Main endpoints:

- `GET /`: Web chatbot interface.
- `GET /health`: Service health check.
- `POST /chat`: Ask a question.
- `GET /sessions/{session_id}`: Read in-memory session history.
- `POST /feedback`: Store answer feedback.
- `POST /settings`: Update runtime LLM API key and base URL for the running process.

## Screenshots

Add screenshots or demo GIFs here after deployment:

```text
docs/screenshots/
```

## Development

Run tests:

```bash
python -m pytest
```

Check formatting and linting:

```bash
python -m ruff check .
python -m black --check .
```

Format code:

```bash
python -m black .
```

## Configuration Notes

- The default `PDF_DIR` is `./raw`; the included sample/source file is `raw/Karshenasi.pdf`.
- The default `WIKI_DIR` is `./wiki`; this directory is used by the chatbot at runtime.
- `VECTOR_DB_PATH` points to rebuildable local data and is ignored by Git.
- Feedback is written to `FEEDBACK_PATH`, defaulting to `./feedback.jsonl`, and is ignored by Git.

## Contributing

1. Create a feature branch.
2. Install development dependencies with `python -m pip install -e ".[all,dev]"`.
3. Add or update tests for behavioral changes.
4. Run `python -m pytest`, `python -m ruff check .`, and `python -m black --check .`.
5. Submit a pull request with a clear summary and test results.

## License

No license file is included yet. Add an explicit license before publishing if you want others to use, modify, or redistribute the project.
