"""Typed data models shared across the analyzer."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TramiteDocument(BaseModel):
    name: str
    required: bool
    uploaded: bool


class TramiteFolio(BaseModel):
    id: str
    ramo: str
    tipo_tramite: str
    monto_prima: float
    requiere_reaseguro: bool
    es_urgente: bool | None = None
    catalog_line: str | None = None
    estatus: str | None = None
    updated_at: datetime | None = None
    documents: List[TramiteDocument] = Field(default_factory=list)


class AnalyzerState(BaseModel):
    id: str
    folio: Optional[TramiteFolio] = None
    signals: dict = Field(default_factory=dict)
    risk: dict = Field(default_factory=dict)
    report: Optional[str] = None


class RiskAssessment(BaseModel):
    score: float
    level: str
    rationale: str
    recommendations: List[str]
