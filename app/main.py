from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import Dict
from .models import TicketRequest, TicketResponse
from .classifier import classify_ticket

app = FastAPI(title="Ticket Triage Agent API")


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    """Serve a minimal HTML UI for interacting with the /triage endpoint."""
    return """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Ticket Triage Agent</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 2rem; background: #0f172a; color: #f9fafb; }
    h1 { margin-bottom: 0.5rem; }
    .card { max-width: 800px; margin: 0 auto; background: #020617; border-radius: 0.75rem; padding: 1.5rem 1.75rem; box-shadow: 0 10px 40px rgba(15,23,42,0.8); border: 1px solid #1f2937; }
    label { display: block; font-size: 0.875rem; margin-bottom: 0.25rem; color: #e5e7eb; }
    textarea, input { width: 100%; box-sizing: border-box; border-radius: 0.5rem; border: 1px solid #374151; background: #020617; color: #f9fafb; padding: 0.5rem 0.75rem; font-size: 0.95rem; }
    textarea:focus, input:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 1px #6366f1; }
    textarea { min-height: 140px; resize: vertical; }
    .field { margin-bottom: 1rem; }
    button { background: #4f46e5; color: white; border: none; border-radius: 999px; padding: 0.55rem 1.4rem; font-size: 0.95rem; font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem; }
    button:hover { background: #6366f1; }
    button:disabled { opacity: 0.6; cursor: default; }
    .pill { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.25rem 0.6rem; border-radius: 999px; font-size: 0.75rem; background: rgba(55,65,81,0.5); color: #e5e7eb; }
    .pill span { width: 6px; height: 6px; border-radius: 999px; background: #22c55e; }
    pre { background: #020617; border-radius: 0.75rem; padding: 0.9rem 1rem; overflow-x: auto; font-size: 0.85rem; border: 1px solid #1f2937; }
    .muted { color: #9ca3af; font-size: 0.85rem; }
    .row { display: flex; gap: 1rem; align-items: center; justify-content: space-between; flex-wrap: wrap; }
  </style>
</head>
<body>
  <div class=\"card\">
    <div class=\"row\">
      <div>
        <h1>Ticket Triage Agent</h1>
        <p class=\"muted\">Paste a support ticket and get category, severity, next steps, and KB match.</p>
      </div>
      <div class=\"pill\"><span></span> <strong>API</strong> online</div>
    </div>

    <div class=\"field\" style=\"margin-top: 1rem;\">
      <label for=\"ticket\">Ticket text</label>
      <textarea id=\"ticket\" placeholder=\"Describe the issue reported by the customer...\"></textarea>
    </div>

    <div class=\"field\">
      <label for=\"client_id\">Client ID (optional)</label>
      <input id=\"client_id\" placeholder=\"e.g. acme-corp\" />
    </div>

    <div class=\"field\">
      <button id=\"submit-btn\" type=\"button\" onclick=\"submitTicket()\">Triage ticket</button>
    </div>

    <div class=\"field\">
      <label>Result</label>
      <pre id=\"result\" class=\"muted\">Waiting for input...</pre>
    </div>
  </div>

  <script>
    async function submitTicket() {
      const ticketEl = document.getElementById('ticket');
      const clientIdEl = document.getElementById('client_id');
      const resultEl = document.getElementById('result');
      const button = document.getElementById('submit-btn');

      const ticket = ticketEl.value.trim();
      const clientId = clientIdEl.value.trim() || null;

      if (!ticket) {
        alert('Please enter a ticket description.');
        return;
      }

      button.disabled = true;
      resultEl.textContent = 'Classifying ticket...';

      try {
        const response = await fetch('/triage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticket: ticket, client_id: clientId })
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error('Request failed: ' + response.status + '\n' + text);
        }

        const data = await response.json();
        resultEl.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        resultEl.textContent = 'Error: ' + err.message;
      } finally {
        button.disabled = false;
      }
    }
  </script>
</body>
</html>
"""


@app.post("/triage", response_model=TicketResponse)
def triage_ticket(request: TicketRequest) -> TicketResponse:
    result = classify_ticket(text=request.ticket, client_id=request.client_id)
    return TicketResponse(**result)
