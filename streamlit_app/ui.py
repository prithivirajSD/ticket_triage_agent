import os
import streamlit as st
import requests
from firebase_config import firebase_analytics_snippet

# -----------------------
# Configuration
# -----------------------
API_BASE = os.getenv("TRIAGE_API_BASE", "https://ticket-triage-agent-3.onrender.com")

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
st.set_page_config(page_title="AI Ticket Triage System", page_icon="🎟️", layout="wide")

# Cache backend status for this render to avoid double calls
backend_alive = backend_is_alive()

# Sidebar status panel
st.sidebar.header("Backend Status")
if backend_alive:
    st.sidebar.success(f"Connected to {API_BASE}")
else:
    st.sidebar.error(
        f"Cannot reach API at {API_BASE}.\n"
        "Start it with: uvicorn main:app --host 127.0.0.1 --port 8000"
    )
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Need help?** Run FastAPI and Streamlit in separate terminals."
)

# Custom styling
st.markdown(
    """
    <style>
        .main {
            background: radial-gradient(circle at top, rgba(99,102,241,0.15), transparent 45%), #080e1c;
            color: #F1F5F9;
        }
        .block-container {
            padding-top: 1.75rem;
            padding-bottom: 3rem;
            max-width: 1180px;
            margin: 0 auto;
        }
        [data-testid="stSidebar"] {
            background: #020617;
            border-right: 1px solid rgba(148,163,184,0.15);
        }
        .surface-card {
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 20px 35px rgba(2,6,23,0.55);
            padding: 1.65rem;
            backdrop-filter: blur(12px);
        }
        .hero-card,
        .info-card,
        .result-card,
        .summary-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 20px 35px rgba(2,6,23,0.55);
            padding: 1.65rem;
            border-radius: 18px;
            backdrop-filter: blur(12px);
        }
        .hero-card h1 {
            margin-top: 0.2rem;
            margin-bottom: 0.65rem;
            font-size: 2rem;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            background: rgba(34,197,94,0.18);
            border: 1px solid rgba(34,197,94,0.35);
            color: #4ade80;
            font-size: 0.85rem;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .two-up {
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }
        .info-card {
            min-height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 0.65rem;
        }
        .metric-pill {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            background: rgba(8, 25, 53, 0.95);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 14px;
            padding: 0.85rem 1rem;
        }
        .metric-pill span {
            font-size: 0.7rem;
            color: #94a3b8;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .metric-pill strong {
            font-size: 1.15rem;
            color: #f1f5f9;
        }
        .stTextInput > div > div > input,
        .stTextArea textarea {
            background: rgba(15, 23, 42, 0.65);
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            color: #E2E8F0;
        }
        [data-testid="stForm"] {
            background: rgba(2, 6, 23, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 22px;
            padding: 1.75rem;
            margin-top: 1.5rem;
            box-shadow: 0 12px 30px rgba(2, 6, 23, 0.6);
        }
        [data-testid="stForm"] .stSubheader {
            margin-top: 0;
        }
        .stButton button {
            border-radius: 999px;
            padding: 0.75rem 2.75rem;
            font-weight: 600;
            background: linear-gradient(120deg, #6366F1, #8B5CF6, #EC4899);
            border: none;
            color: white;
            box-shadow: 0 12px 24px rgba(99,102,241,0.35);
        }
        .stButton button:disabled {
            opacity: 0.35;
            box-shadow: none;
        }
        ul, ol {
            padding-left: 1.3rem;
            margin-bottom: 0;
        }
        .meta-card p {
            margin-bottom: 0.6rem;
        }
        .subdued-text {
            color: #cbd5f5;
            font-size: 0.9rem;
        }
        @media (max-width: 768px) {
            .hero-card h1 {
                font-size: 1.65rem;
            }
            .info-card {
                min-height: auto;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Top navigation / branding
st.markdown(
    """
    <div class="surface-card" style="padding:0.75rem 1.5rem; margin-bottom:1.5rem; display:flex; align-items:center; justify-content:space-between; gap:1rem;">
        <div>
            <strong style="font-size:1rem; letter-spacing:0.08em; text-transform:uppercase; color:#94a3b8;">Ticket Triage Agent</strong>
            <div class="subdued-text">AI-powered ops assistant for support teams</div>
        </div>
        <div class="status-pill">API backend ready ✅</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Hero + overview section
hero_left, hero_right = st.columns([3, 2])
with hero_left:
    st.markdown(
        """
        <div class="hero-card">
            <div class="status-pill">🎯 AI Ticket Routing</div>
            <h1>Ticket Triage Command Center</h1>
            <p class="subdued-text" style="max-width: 65ch;">
                Send customer tickets to the FastAPI brain, get instant AI-powered summaries,
                recommended next steps, and Firestore-ready metadata.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_right:
    st.markdown(
        """
        <div class="info-card" style="gap:1rem;">
            <div>
                <h4 style="margin-top:0; margin-bottom:0.4rem;">Run checklist</h4>
                <ol>
                    <li>Start FastAPI backend (uvicorn).</li>
                    <li>Launch this Streamlit app.</li>
                    <li>Set <code>TRIAGE_API_BASE</code> to backend URL.</li>
                </ol>
            </div>
            <p class="subdued-text" style="margin-bottom:0;">Use separate terminals so the UI stays responsive while the API handles requests.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Guidance cards row (aligned grid)
st.markdown(
    """
    <div class="info-grid two-up">
        <div class="info-card">
            <div>
                <h4 style="margin-top:0;">How to use</h4>
                <p class="subdued-text">Keep these best practices handy:</p>
            </div>
            <ul>
                <li>Enter a descriptive Client ID.</li>
                <li>Paste the raw ticket with detail + urgency.</li>
                <li>Click <strong>Classify Ticket</strong> to analyze.</li>
            </ul>
        </div>
        <div class="info-card">
            <div>
                <h4 style="margin-top:0;">Pro tips</h4>
                <p class="subdued-text">Lift accuracy with richer metadata:</p>
            </div>
            <ul>
                <li>Mention environment + recent changes.</li>
                <li>Flag severity or customer impact.</li>
                <li>Reference known incident IDs.</li>
            </ul>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Ticket form
with st.form("ticket_form"):
    st.subheader("Classify a new ticket")
    form_col1, form_col2 = st.columns([1, 2])
    with form_col1:
        client_id = st.text_input(
            "Client ID",
            help="Unique ID of the user raising the ticket",
        )
        st.caption("Example: ACME-SRE-01")
    with form_col2:
        ticket_text = st.text_area(
            "Support Ticket",
            height=220,
            placeholder="Describe the customer issue, context, and urgency...",
        )

    submitted = st.form_submit_button(
        "Classify Ticket",
        disabled=not backend_alive,
        use_container_width=True,
    )

# Firebase analytics snippet (hidden)
st.components.v1.html(firebase_analytics_snippet(), height=0)

# Session state for results
if "classification" not in st.session_state:
    st.session_state["classification"] = None

if submitted:
    if not client_id.strip():
        st.warning("Please enter a client ID before classification.")
    elif not ticket_text.strip():
        st.warning("Please enter a ticket before classification.")
    else:
        try:
            st.session_state["classification"] = classify_ticket(ticket_text, client_id)
        except requests.HTTPError as http_err:
            st.error(f"HTTP error while calling API: {http_err}")
        except requests.RequestException as req_err:
            st.error(f"Request error: {req_err}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# Render results if available
if st.session_state["classification"]:
    data = st.session_state["classification"]
    st.subheader("Ticket Classification Result")

    summary_col, meta_col = st.columns([2, 1])
    with summary_col:
        st.markdown(
            f"""
            <div class="result-card">
                <h3 style="margin-bottom:0.5rem;">Summary</h3>
                <p style="color:#CBD5F5; font-size:1.05rem;">{data.get('summary', 'No summary')}</p>
                <div class="info-grid">
                    <div class="metric-pill"><span>Client</span><strong>{data.get('client_id', client_id)}</strong></div>
                    <div class="metric-pill"><span>Category</span><strong>{data.get('category', 'Uncategorized')}</strong></div>
                    <div class="metric-pill"><span>Severity</span><strong>{data.get('severity', 'Medium')}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with meta_col:
        st.markdown(
            f"""
            <div class="result-card">
                <p><strong>KB Match:</strong><br>{data.get('kb_match', 'None')}</p>
                <p><strong>Next Step:</strong><br>{data.get('next_step', 'Pending')}</p>
                <p><strong>Analysis Source:</strong><br>{data.get('analysis_source', 'Unknown')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="result-card" style="margin-top: 0.5rem;">
            <h4>Full Ticket</h4>
            <p style="white-space: pre-wrap;">{data.get('full_text', 'No text available')}</p>
            <h4>Full LLM Summary</h4>
            <p style="white-space: pre-wrap;">{data.get('full_summary', 'No full summary available')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Raw LLM Data"):
        st.json(data.get("llm_raw", {}))
