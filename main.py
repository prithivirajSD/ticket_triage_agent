# app/main.py
from fastapi import FastAPI
from typing import Dict
from app.models import TicketRequest, TicketResponse
from app.classifier import classify_ticket

app = FastAPI(title="Ticket Triage Agent API")

@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Ticket Triage Agent API is running."}

@app.post("/triage", response_model=TicketResponse)
def triage_ticket(request: TicketRequest):
    result = classify_ticket(request.ticket)
    return result
