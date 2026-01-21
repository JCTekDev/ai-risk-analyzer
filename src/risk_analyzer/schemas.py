"""Typed data models shared across the analyzer."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TramiteDocument(BaseModel):
    name: str
    required: bool
    uploaded: bool


class TramiteFolio(BaseModel):
    folio_id: str = Field(alias="folio")
    ramo: str
    tipo_tramite: str
    monto_prima: float
    requiere_reaseguro: bool
    es_urgente: bool | None = None
    catalog_line: str | None = None
    estatus: str | None = None
    updated_at: datetime | None = None
    documents: List[TramiteDocument] = Field(default_factory=list)

    @field_validator("folio_id", mode="before")
    @classmethod
    def fallback_to_id(cls, v: str | None, info) -> str:
        """If folio is not provided, use id field as fallback."""
        if v:
            return v
        # Check if id is in the input data
        if hasattr(info, "data") and "id" in info.data:
            return info.data["id"]
        raise ValueError("folio_id must be provided (via 'folio' or 'id' field)")


class AnalyzerState(BaseModel):
    folio_id: str
    folio: Optional[TramiteFolio] = None
    signals: dict = Field(default_factory=dict)
    risk: dict = Field(default_factory=dict)
    report: Optional[str] = None


class RiskAssessment(BaseModel):
    score: float
    level: str
    rationale: str
    recommendations: List[str]
