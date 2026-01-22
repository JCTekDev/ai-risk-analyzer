"""Deterministic heuristics for risk scoring."""

from __future__ import annotations

import logging
from typing import Iterable

from .schemas import RiskAssessment, TramiteFolio


logger = logging.getLogger(__name__)


def heuristic_score(folio: TramiteFolio, *, signals: dict | None = None) -> RiskAssessment:
    """Produce a baseline risk score before LLM adjustment."""

    signal_keys = sorted(signals.keys()) if isinstance(signals, dict) else []
    logger.debug(
        "Starting heuristic scoring folio=%s ramo=%s prima=%.2f signals=%s",
        folio.id,
        folio.ramo,
        folio.monto_prima,
        signal_keys,
    )

    score = 0.0
    recommendations: list[str] = []

    if folio.ramo.lower() in {"daños", "vida"} and folio.monto_prima >= 1_000_000:
        score += 0.6
        recommendations.append("Validar exposición por monto alto en ramo crítico")
        logger.debug(
            "Applied critical ramo premium rule folio=%s ramo=%s prima=%.2f increment=0.60",
            folio.id,
            folio.ramo,
            folio.monto_prima,
        )

    if folio.requiere_reaseguro:
        score += 0.25
        recommendations.append("Confirmar capacidad de reasegurador")
        logger.debug("Applied reinsurance rule folio=%s increment=0.25", folio.id)

    missing_docs = _count_missing_docs(folio.documents)
    if missing_docs:
        increment = min(0.15, missing_docs * 0.05)
        score += increment
        recommendations.append(f"Solicitar {missing_docs} documentos faltantes")
        logger.debug(
            "Applied missing docs rule folio=%s missing=%d increment=%.2f",
            folio.id,
            missing_docs,
            increment,
        )

    if folio.es_urgente is True:
        score += 0.1
        recommendations.append("Priorizar folio urgente en cola")
        logger.debug("Applied urgency rule folio=%s increment=0.10", folio.id)

    score = max(0.0, min(1.0, score))
    level = "alto" if score >= 0.7 else "medio" if score >= 0.4 else "bajo"
    rationale = (
        f"Riesgo {level} generado por ramo {folio.ramo}, prima {folio.monto_prima}, "
        f"reaseguro {'sí' if folio.requiere_reaseguro else 'no'} y {missing_docs} docs faltantes"
    )

    logger.info(
        "Heuristic score complete folio=%s score=%.2f level=%s missing_docs=%d recommendations=%d",
        folio.id,
        score,
        level,
        missing_docs,
        len(recommendations),
    )

    return RiskAssessment(score=score, level=level, rationale=rationale, recommendations=recommendations)


def _count_missing_docs(documents: Iterable) -> int:
    return sum(1 for doc in documents if getattr(doc, "required", False) and not getattr(doc, "uploaded", False))
