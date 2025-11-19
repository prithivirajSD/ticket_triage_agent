from pydantic import BaseModel, Field
from typing import Optional


class TicketRequest(BaseModel):
    client_id: str = Field(..., description="Identifier for the client/user raising the ticket")
    ticket: str = Field(..., description="The support ticket text to classify")


class TicketResponse(BaseModel):
    client_id: str = Field(..., description="Identifier for the client/user raising the ticket")
    summary: str = Field(..., description="Human-friendly summary of the ticket")
    full_summary: Optional[str] = Field(None, description="Full LLM-generated summary when available")
    full_text: str = Field(..., description="Original ticket text")
    category: str = Field(..., description="Ticket category")
    severity: str = Field(..., description="Severity level")
    kb_match: Optional[str] = Field(None, description="Matching KB entry ID if found")
    next_step: str = Field(..., description="Recommended next action")
    analysis_source: str = Field(..., description="Which engine produced the analysis")
    llm_raw: Optional[dict] = Field(None, description="Raw JSON returned by the LLM")