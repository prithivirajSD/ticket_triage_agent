<<<<<<< HEAD
# Ticket Triage Agent

AI-powered ticket triage platform that:

1. Collects tickets from a Streamlit UI (with client ID attribution).
2. Calls a FastAPI backend that combines Groq LLM reasoning with a curated knowledge base (`data/knowledge_base.json`).
3. Persists every ticket + classification result to Firebase Firestore under an issue/ severity hierarchy.

## Architecture

| Component | Purpose |
|-----------|---------|
| `FastAPI` | `/triage` endpoint that calls `classify_ticket` |
| `Groq LLM` | Generates AI summary, category, severity, KB match, recommended next step |
| `Knowledge Base` | Fallback + grounding for issue IDs (ISSUE-00x) |
| `Firebase Firestore` | Stores tickets under `tickets/{ISSUE_ID}/{Severity}` |
| `Streamlit UI` | Collects `client_id`, ticket text, and displays results |

## Prerequisites

- Python 3.11+
- A Groq API key (https://console.groq.com)
- Firebase project with Firestore enabled (service-account JSON)
- Optional: Docker (for container-based deployment)

## Project Layout

```
ticket-triage-agent/
├── app/                # FastAPI app, classifier, Firebase client
├── streamlit_app/      # Streamlit frontend
├── data/knowledge_base.json
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Environment Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=sk_your_key
GROQ_MODEL=llama-3.1-8b-instant   # optional override
FIREBASE_CREDENTIALS=C:\\path\\to\\serviceAccountKey.json
ALLOW_LOCAL_FALLBACK=0           # optional; set to 1 to allow JSONL fallback
TRIAGE_API_BASE=http://localhost:8000  # used by Streamlit
```

Place your Firebase service account JSON either at the path referenced by `FIREBASE_CREDENTIALS` or as `firebase_key.json` in the project root.

## Setup & Local Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1. Start FastAPI backend

```bash
uvicorn main:app --reload
# or `uvicorn app.main:app --reload` if you prefer module path
```

The API exposes:
- `GET /` – health check
- `POST /triage` – body `{"client_id": "CUST-123", "ticket": "..."}`

### 2. Start Streamlit UI (new terminal)

```bash
streamlit run streamlit_app/ui.py
```

Provide `Client ID` and ticket text. Results include summary, KB match, next step, severity, raw LLM JSON. Every request is persisted to Firestore.

## Firestore Data Model

```
tickets (collection)
├── ISSUE-001 (document)
│   ├── High (subcollection)
│   │   └── <ticket doc>
│   └── Medium
├── ISSUE-002
└── NEW_ISSUES (fallback when no KB match)
```

Each ticket doc stores:

- `client_id`, `ticket`, `summary`, `category`, `severity`
- `kb_match`, `next_step`, `analysis_source`
- `llm_raw`, `created_at`

## Testing

```bash
pytest
```

The test suite posts a sample ticket and asserts category/severity/kb match.

## Deployment

### Environment Variables

Ensure the same `.env` values are present on your server/hosting platform (or configure them directly in the environment).

### Docker (optional)

```
docker build -t ticket-triage-agent .
docker run --env-file .env -p 8000:8000 ticket-triage-agent
```

Serve the Streamlit UI separately (Streamlit Cloud, internal host, etc.) and point `TRIAGE_API_BASE` to the deployed API URL.

### Firebase

- Enable Firestore in Native mode.
- Upload the service account JSON and set `FIREBASE_CREDENTIALS`.
- Confirm Firestore security rules before exposing publicly.

### Monitoring & Logging

- FastAPI logs via Uvicorn.
- Streamlit logs in its terminal.
- Firestore writes are logged in `app/firebase_client.py`.

## Troubleshooting

- **Groq 400 error** – model deprecated → change `GROQ_MODEL`.
- **Firestore unavailable** – ensure credentials path is correct or set `ALLOW_LOCAL_FALLBACK=1` to capture tickets in `data/ticket_results.jsonl`.
- **Streamlit cannot reach API** – verify FastAPI is running on the port configured in `TRIAGE_API_BASE`.

## Contributing

- Update `data/knowledge_base.json` to tweak KB entries.
- Run `pytest` before opening PRs.
- Follow PEP8 / `ruff` guidelines if adding linting.
=======
# ticket_triage_agent
LLM project
>>>>>>> d665926e6fab5f88b7f9478d76b66e6723460934
