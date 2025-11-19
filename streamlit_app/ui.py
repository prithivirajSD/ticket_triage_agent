import os
import streamlit as st
import requests
from firebase_config import firebase_analytics_snippet

# -----------------------
# Configuration
# -----------------------
API_BASE = os.getenv("TRIAGE_API_BASE", "http://localhost:8000")

# -----------------------
# Helper functions
# -----------------------
def backend_is_alive() -> bool:
    """Check if the backend API is reachable."""
    try:
        response = requests.get(f"{API_BASE}/", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def classify_ticket(ticket_text: str, client_id: str) -> dict:
    """Call the backend API to classify a ticket."""
    payload = {
        "client_id": client_id,
        "ticket": ticket_text,
    }
    response = requests.post(
        f"{API_BASE}/triage",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="AI Ticket Triage System", layout="wide")
st.title("AI Ticket Triage System")
st.sidebar.header("Backend Status")

# Show backend connection status
if backend_is_alive():
    st.sidebar.success(f"Connected to {API_BASE}")
else:
    st.sidebar.error(
        f"Cannot reach API at {API_BASE}.\n"
        "Start it with: uvicorn main:app --host 127.0.0.1 --port 8000"
    )

# Client/ticket inputs
client_id = st.text_input("Client ID", help="Unique ID of the user raising the ticket")
ticket_text = st.text_area("Enter your support ticket:", height=150)

# Firebase analytics snippet (hidden)
st.components.v1.html(firebase_analytics_snippet(), height=0)

# Classify button
if st.button("Classify Ticket", disabled=not backend_is_alive()):
    if not client_id.strip():
        st.warning("Please enter a client ID before classification.")
    elif not ticket_text.strip():
        st.warning("Please enter a ticket before classification.")
    else:
        try:
            data = classify_ticket(ticket_text, client_id)

            st.subheader("Ticket Classification Result")

            st.markdown(f"**Client ID:** {data.get('client_id', client_id)}")

            # Summary
            st.markdown(f"**Summary:** {data.get('summary', 'No summary')}")
            st.markdown(f"**Full LLM Summary (Corrected):** {data.get('full_summary', 'No full summary available')}")
            # Full ticket text
            st.markdown(f"**Full Ticket Text:** {data.get('full_text', 'No text available')}")
            # Other fields
            st.markdown(f"**Category:** {data.get('category', 'Uncategorized')}")
            st.markdown(f"**Severity:** {data.get('severity', 'Medium')}")
            st.markdown(f"**Knowledge Base Match:** {data.get('kb_match', 'None')}")
            st.markdown(f"**Next Step:** {data.get('next_step', 'Pending')}")
            st.markdown(f"**Analysis Source:** {data.get('analysis_source', 'Unknown')}")

            # Raw LLM output
            with st.expander("Raw LLM Data"):
                st.json(data.get('llm_raw', {}))

        except requests.HTTPError as http_err:
            st.error(f"HTTP error while calling API: {http_err}")
        except requests.RequestException as req_err:
            st.error(f"Request error: {req_err}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
