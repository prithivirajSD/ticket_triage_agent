from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_payment_ticket():
    ticket = {
        "client_id": "test-client",
        "ticket": "Payment failed with error 500 during checkout",
    }
    response = client.post("/triage", json=ticket)
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "test-client"
    assert data["category"] == "Payment"
    assert data["severity"].lower() in ["high", "medium", "low", "critical"]
    assert data["kb_match"] == "ISSUE-001"
