"""LangGraph application wiring for the risk analyzer."""

from __future__ import annotations

import json
from typing import Any, Callable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph

from .joget_adapter import JogetClient
from .schemas import AnalyzerState, RiskAssessment
from .scoring import heuristic_score


PromptFactory = Callable[[], ChatPromptTemplate]


def build_app(
    *,
    llm: Runnable | None = None,
    joget_client: JogetClient | None = None,
    prompt_factory: PromptFactory | None = None,
):
    """Create and compile the LangGraph application."""

    client = joget_client or JogetClient()
    prompt = prompt_factory() if prompt_factory else _default_prompt()

    def fetch_tramite(state: AnalyzerState) -> dict[str, Any]:
        folio = client.fetch_tramite(state.folio_id)
        signals = {
            "missing_docs": [doc.name for doc in folio.documents if doc.required and not doc.uploaded],
            "ramo": folio.ramo,
            "requiere_reaseguro": folio.requiere_reaseguro,
        }
        return {"folio": folio, "signals": signals}

    def enrich_context(state: AnalyzerState) -> dict[str, Any]:
        signals = dict(state.signals)
        if state.folio and state.folio.catalog_line:
            signals["catalog_line"] = state.folio.catalog_line
        if state.folio and state.folio.estatus:
            signals["estatus"] = state.folio.estatus
        return {"signals": signals}

    def score_risk(state: AnalyzerState) -> dict[str, Any]:
        assert state.folio, "Folio data missing before scoring"
        assessment = heuristic_score(state.folio, signals=state.signals)
        delta = 0.0
        rationale = assessment.rationale
        recommendations = list(assessment.recommendations)

        if llm is not None:
            llm_payload = {
                "folio": state.folio.model_dump(),
                "signals": state.signals,
                "baseline": assessment.model_dump(),
            }
            llm_chain = prompt | llm | StrOutputParser()
            raw = llm_chain.invoke(llm_payload)
            try:
                parsed = json.loads(raw)
                delta = float(parsed.get("delta", 0.0))
                rationale = parsed.get("rationale", rationale)
                recommendations.extend(parsed.get("recommendations", []))
            except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                recommendations.append("LLM no devolvió JSON válido; se conserva baseline")
        final_score = max(0.0, min(1.0, assessment.score + delta))
        level = "alto" if final_score >= 0.7 else "medio" if final_score >= 0.4 else "bajo"
        risk = RiskAssessment(
            score=final_score,
            level=level,
            rationale=rationale,
            recommendations=recommendations,
        )
        return {"risk": risk.model_dump()}

    def render_report(state: AnalyzerState) -> dict[str, Any]:
        assert state.folio and state.risk
        risk = RiskAssessment.model_validate(state.risk)
        missing_docs = state.signals.get("missing_docs", [])
        report = [
            f"Folio **{state.folio.folio_id}**",
            f"Nivel de riesgo: **{risk.level.upper()}** ({risk.score:.2f})",
            f"Motivo: {risk.rationale}",
        ]
        if missing_docs:
            report.append(f"Documentos faltantes: {', '.join(missing_docs)}")
        if risk.recommendations:
            report.append("Recomendaciones:")
            for item in risk.recommendations:
                report.append(f"- {item}")
        return {"report": "\n".join(report)}

    graph = StateGraph(AnalyzerState)
    graph.add_node("fetch_tramite", fetch_tramite)
    graph.add_node("enrich_context", enrich_context)
    graph.add_node("score_risk", score_risk)
    graph.add_node("render_report", render_report)

    graph.set_entry_point("fetch_tramite")
    graph.add_edge("fetch_tramite", "enrich_context")
    graph.add_edge("enrich_context", "score_risk")
    graph.add_edge("score_risk", "render_report")
    graph.add_edge("render_report", END)

    return graph.compile()


def _default_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un analista de riesgo. Devuelve JSON con keys delta (entre -0.2 y 0.4), "
                "rationale y recommendations. Considera señales y baseline." ,
            ),
            (
                "human",
                "Folio: {folio}\nSeñales: {signals}\nBaseline: {baseline}",
            ),
        ]
    )
