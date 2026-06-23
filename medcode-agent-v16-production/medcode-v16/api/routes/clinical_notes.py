"""
Clinical Notes Routes — Parse clinical notes for CPT and ICD-10 coding.
=========================================================================
POST /api/v19/clinical-notes/parse  — Parse a clinical note
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v19/clinical-notes", tags=["clinical-notes"])


class ClinicalNoteParseRequest(BaseModel):
    note_text: str
    note_type: Optional[str] = "progress"

    class Config:
        max_text_length = 100000


def _get_parser():
    from agents.clinical_note_parser import ClinicalNoteParser
    return ClinicalNoteParser()


@router.post("/parse")
async def parse_clinical_note(body: ClinicalNoteParseRequest):
    """Parse a clinical note and return coding suggestions with confidence scores."""
    if not body.note_text or not body.note_text.strip():
        raise HTTPException(status_code=400, detail="note_text is required and cannot be empty")

    try:
        parser = _get_parser()
        result = parser.parse(body.note_text)
        result["note_type"] = body.note_type
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")
