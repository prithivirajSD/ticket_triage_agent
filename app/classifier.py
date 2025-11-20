import os
import re
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import requests
from dotenv import load_dotenv  # Used for loading .env file
from .firebase_client import save_ticket_result as save_ticket_to_firestore

# ======================================================
# 🔧 Setup & Logging
# ======================================================

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Correctly read the API key/model from the environment
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

# ======================================================
# 📘 Load Knowledge Base
# ======================================================
# Navigate up from 'app' directory to the project root, then into 'data'
KB_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base.json"

def load_kb() -> list:
    """Loads the knowledge base JSON file."""
    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            log.info(f"Successfully loaded knowledge base from {KB_PATH}.")
            return json.load(f)
    except FileNotFoundError:
        log.error(f"Knowledge Base file not found at: {KB_PATH}. Returning empty list.")
        return []
    except Exception as e:
        log.error(f"Failed to load KB: {e}")
        return []

KB = load_kb()


def _kb_prompt_context(max_entries: int = 20) -> str:
    """Formats KB entries for inclusion in the LLM prompt."""
    if not KB:
        return "No knowledge base entries available."

    rows = []
    for entry in KB[:max_entries]:
        symptoms = ", ".join(entry.get("symptoms", [])) or "(no symptoms listed)"
        rows.append(
            f"{entry.get('id')}: {entry.get('title')} | "
            f"Category={entry.get('category')} | Symptoms={symptoms} | "
            f"Recommended Action={entry.get('recommended_action')}"
        )
    return "\n".join(rows)


def _get_kb_entry_by_id(issue_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not issue_id:
        return None
    normalized = issue_id.strip()
    for entry in KB:
        if entry.get("id", "").strip().lower() == normalized.lower():
            return entry
    return None


# ======================================================
# 🔥 KB Matching (Symptom-based scoring)
# ======================================================
def _find_kb_entry(text: str) -> Optional[Dict[str, Any]]:
    """Finds the best matching KB entry based on symptom keywords."""
    text = text.lower()
    best_match = None
    best_score = 0

    for entry in KB:
        score = 0
        # Symptoms are case-insensitive and checked for presence in the ticket text
        for symptom in entry.get("symptoms", []):
            if symptom.lower() in text:
                score += 1

        if score > best_score:
            best_match = entry
            best_score = score
            
    if best_score > 0:
        log.info(f"KB Match found with score {best_score} for ID: {best_match.get('id')}")
    else:
        log.info("No strong KB match found.")

    return best_match if best_score > 0 else None


# ======================================================
# 🧠 Severity Helpers
# ======================================================
def _normalize_severity(value: Optional[str]) -> Optional[str]:
    """Normalizes severity strings to predefined levels."""
    if not value:
        return None
    value = value.lower().strip()

    mapping = {
        "critical": "Critical",
        "blocker": "Critical",
        "urgent": "High",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }
    # Defaults to Medium if the LLM output is unrecognized
    return mapping.get(value, "Medium")


def _infer_severity(text: str) -> str:
    """Infers severity based on simple keywords as a fallback."""
    lower = text.lower()
    if any(w in lower for w in ["crash", "down", "failed", "cannot", "error", "not working", "system is unavailable"]):
        return "High"
    if "slow" in lower or "request" in lower or "question" in lower:
        return "Low"
    return "Medium"


# ======================================================
# ✨ JSON Auto-Repair
# ======================================================
def _repair_json(text: str) -> dict:
    """Attempts to repair common LLM JSON formatting errors."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass # Fall through to repair logic

    # Simple cleanup: replace single quotes with double quotes, remove newlines, remove trailing commas
    cleaned = (
        text.replace("'", '"')
        .replace("\n", " ")
    )
    cleaned = re.sub(r",\s*}", "}", cleaned)
    cleaned = re.sub(r",\s*]", "]", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.error(f"Failed to repair and load JSON: {e}. Raw text: {text}")
        return {}
    except Exception as e:
        log.error(f"Unexpected error during JSON repair: {e}")
        return {}


def _correct_summary(summary: Optional[str]) -> Optional[str]:
    """Lightweight cleanup for LLM summaries (strip whitespace, fix spacing)."""
    if not summary:
        return None
    cleaned = " ".join(summary.split())
    return cleaned.strip() or None


# ======================================================
# 🤖 Groq LLM Classification
# ======================================================
def _llm_classification(text: str) -> Dict[str, Any]:
    """Calls the Groq API to classify the ticket using Mixtral."""
    if not GROQ_API_KEY:
        log.warning("No Groq API key found. Skipping LLM classification.")
        return {}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    kb_context = _kb_prompt_context()
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert IT ticket classifier. "
                    "Use the knowledge base entries to pick the closest issue ID. "
                    "Always respond with strict JSON containing these keys: "
                    "summary (string), category (string), severity (Critical|High|Medium|Low), "
                    "kb_issue_id (string, one of the provided KB IDs or 'NEW_ISSUE'), "
                    "kb_issue_title (string), next_step (string with the best recommended action)."
                )
            },
            {
                "role": "user",
                "content": (
                    "Knowledge Base Entries:\n"
                    f"{kb_context}\n\n"
                    "Ticket to Analyze:\n"
                    f"{text}\n\n"
                    "Return ONLY JSON. Choose kb_issue_id from the KB list when possible; "
                    "otherwise respond with 'NEW_ISSUE'."
                ),
            },
        ],
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
        data = r.json()

        if not data.get("choices"):
            log.error(f"Groq LLM response missing 'choices'. Response data: {data}")
            return {}

        raw = data["choices"][0]["message"]["content"].strip()
        log.info("LLM responded successfully.")
        return _repair_json(raw)

    except requests.exceptions.HTTPError as e:
        log.error(f"Groq LLM HTTP Error: {e.response.status_code} - {e.response.text}")
        return {}
    except requests.exceptions.RequestException as e:
        log.error(f"Groq LLM Request Exception: {e}")
        return {}
    except Exception as e:
        log.error(f"Groq LLM Unexpected Exception: {e}")
        return {}


# ======================================================
# 📝 Save Logs
# ======================================================
def save_ticket_result(ticket_text: str, classification: Dict[str, Any]) -> None:
    """Persist ticket + classification to Firestore via firebase_client.

    Falls back to local JSONL only if firebase_client is configured that way.
    """
    try:
        # Store original user input and raw LLM output (if any) together
        payload: Dict[str, Any] = {
            "original_input": ticket_text,
            **classification,
        }
        save_ticket_to_firestore(ticket_text, payload)
        log.info("Ticket classification stored via firebase_client.")
    except Exception as e:
        log.error(f"Failed to persist ticket via firebase_client: {e}")


# ======================================================
# 🚀 MAIN CLASSIFICATION PIPELINE
# ======================================================
from typing import Dict, Any

def classify_ticket(text: str, client_id: str | None = None) -> Dict[str, Any]:
    """
    Classify a ticket and generate a corrected LLM summary.
    """
    llm_result = _llm_classification(text)  # AI classification (summary/category/severity/kb/next step)

    # Determine KB issue from LLM first, fall back to symptom matching
    kb = _get_kb_entry_by_id(llm_result.get("kb_issue_id") if llm_result else None)
    if not kb:
        kb = _find_kb_entry(text)

    kb_id = kb.get("id") if kb else None
    kb_category = kb.get("category") if kb else None
    kb_title = kb.get("title") if kb else None
    kb_action = kb.get("recommended_action") if kb else None

    # Original LLM summary
    llm_summary = llm_result.get("summary") if llm_result else None

    # Correct and improve LLM summary using a function
    corrected_summary = _correct_summary(llm_summary) if llm_summary else None

    # Build final summary for display: prioritize corrected LLM summary -> KB title -> truncated text
    summary = corrected_summary or kb_title or text[:80]

    # Category & severity: rely on Groq first; fall back to KB / heuristics when missing
    category = (llm_result.get("category") if llm_result else None) or kb_category or "General"
    severity = _normalize_severity(llm_result.get("severity")) if llm_result else None
    severity = severity or _infer_severity(text)

    # Next step: prefer AI recommendation, then KB action, then default
    next_step = (llm_result.get("next_step") if llm_result else None) or kb_action or "Investigate and escalate to support."

    result: Dict[str, Any] = {
        "client_id": client_id or "unknown-client",
        "summary": summary,                  # prioritized, corrected summary
        "full_summary": corrected_summary,   # full corrected LLM summary
        "full_text": text,                   # original ticket text
        "category": category,
        "severity": severity,
        "kb_match": kb_id,
        "next_step": next_step,
        "analysis_source": "Groq+KB" if (llm_result and kb_id) else ("Groq" if llm_result else "Heuristics"),
        "llm_raw": llm_result
    }

    save_ticket_result(ticket_text=text, classification=result)
    return result

