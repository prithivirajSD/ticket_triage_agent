from fastapi import FastAPI
from typing import Dict
from .models import TicketRequest, TicketResponse
from .classifier import classify_ticket

app = FastAPI(title="Ticket Triage Agent API")


@app.get("/")
def root() -> Dict[str, str]:
    """Plain JSON health check so FastAPI stays API-only."""
    return {
        "message": "Ticket Triage Agent API is running.",
        "triage_endpoint": "/triage",
    }


@app.post("/triage", response_model=TicketResponse)
def triage_ticket(request: TicketRequest) -> TicketResponse:
    result = classify_ticket(text=request.ticket, client_id=request.client_id)
    return TicketResponse(**result)
