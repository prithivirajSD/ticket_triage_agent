from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, MutableMapping

LOGGER = logging.getLogger(__name__)
CREDENTIAL_ENV = "FIREBASE_CREDENTIALS"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CREDENTIAL_PATH = PROJECT_ROOT / "firebase_key.json"
LOCAL_FALLBACK_PATH = PROJECT_ROOT / "data" / "ticket_results.jsonl"
ALLOW_LOCAL_FALLBACK = os.getenv("ALLOW_LOCAL_FALLBACK", "1").lower() in {"1", "true", "yes"}

# Root collection for issues. Each document groups tickets for a single issue
ISSUE_COLLECTION = "tickets"

_FIREBASE_APP: Any | None = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    credentials = None
    firestore = None

def _credential_path() -> Path | None:
    explicit = os.getenv(CREDENTIAL_ENV)
    if explicit and Path(explicit).exists():
        return Path(explicit)
    if DEFAULT_CREDENTIAL_PATH.exists():
        return DEFAULT_CREDENTIAL_PATH
    return None

def _init_app():
    global _FIREBASE_APP
    if _FIREBASE_APP:
        return _FIREBASE_APP
    if not firebase_admin or not credentials:
        return None
    cred_path = _credential_path()
    if not cred_path:
        return None
    try:
        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            _FIREBASE_APP = firebase_admin.initialize_app(cred)
        else:
            _FIREBASE_APP = firebase_admin.get_app()
        return _FIREBASE_APP
    except Exception as exc:
        LOGGER.warning("Failed to initialize Firebase app: %s", exc)
        return None

def get_firestore_client() -> Any:
    app = _init_app()
    if not app or not firestore:
        return None
    try:
        return firestore.client(app=app)
    except Exception as exc:
        LOGGER.warning("Unable to create Firestore client: %s", exc)
        return None

def _build_payload(ticket_text: str, classification: MutableMapping[str, Any]) -> dict[str, Any]:
    payload = {
        "ticket": ticket_text,
        "client_id": classification.get("client_id", "unknown-client"),
        **classification,
    }
    payload["created_at"] = datetime.now(timezone.utc).isoformat()
    return payload

def _severity_bucket(severity: str | None) -> str:
    """Normalize severity to one of the known buckets used as subcollection names."""
    if not severity:
        return "Medium"
    normalized = severity.strip().capitalize()
    if normalized not in {"Low", "Medium", "High", "Critical"}:
        return "Medium"
    return normalized


def _persist_to_firestore(payload: MutableMapping[str, Any], classification: MutableMapping[str, Any]) -> bool:
    client = get_firestore_client()
    if not client:
        return False

    try:
        kb_id = classification.get("kb_match")

        # 1) Choose or create the issue document under ISSUE_COLLECTION
        if kb_id:
            # Known issue from KB.json (e.g. ISSUE-001, ISSUE-002)
            issue_id = str(kb_id)
        else:
            # All tickets without a KB match are grouped under a single logical bucket
            issue_id = "NEW_ISSUES"
            classification["kb_match"] = issue_id
            classification["kb_source"] = "auto_generated"

        issue_ref = client.collection(ISSUE_COLLECTION).document(issue_id)

        # 2) Update issue-level metadata (summary/category/action)
        issue_metadata: dict[str, Any] = {
            "issue_id": classification.get("kb_match"),
            "title": classification.get("summary", "Untitled issue"),
            "category": classification.get("category", "General"),
            "recommended_action": classification.get("next_step", "Investigate"),
            "source": classification.get("kb_source", "knowledge_base"),
        }
        if firestore:
            issue_metadata["updated_at"] = firestore.SERVER_TIMESTAMP
        else:
            issue_metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        issue_ref.set(issue_metadata, merge=True)

        # 3) Store individual ticket under a severity subcollection for this issue
        firestore_payload = dict(payload)
        if firestore:
            firestore_payload["created_at"] = firestore.SERVER_TIMESTAMP

        severity = _severity_bucket(classification.get("severity"))
        severity_collection = issue_ref.collection(severity)
        severity_collection.add(firestore_payload)

        return True
    except Exception as exc:
        LOGGER.warning("Failed to save ticket to Firestore: %s", exc)
        return False

def _persist_locally(payload: MutableMapping[str, Any]) -> bool:
    try:
        LOCAL_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOCAL_FALLBACK_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        LOGGER.error("Failed to persist ticket locally: %s", exc)
        return False

def save_ticket_result(ticket_text: str, classification: MutableMapping[str, Any]) -> bool:
    payload = _build_payload(ticket_text, classification)
    if _persist_to_firestore(payload, classification):
        return True
    if not ALLOW_LOCAL_FALLBACK:
        raise RuntimeError("Firestore failed and local fallback disabled.")
    LOGGER.info("Saving ticket locally at %s", LOCAL_FALLBACK_PATH)
    return _persist_locally(payload)
