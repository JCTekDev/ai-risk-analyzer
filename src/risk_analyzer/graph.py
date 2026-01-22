"""LangGraph application wiring for the risk analyzer."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph

from .joget_adapter import JogetClient
from .schemas import AnalyzerState, RiskAssessment
from .scoring import heuristic_score


logger = logging.getLogger(__name__)
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
        logger.info(f"fetch_tramite: Loading id={state.id}")
        folio = client.fetch_tramite(state.id)
        logger.debug(f"fetch_tramite: Received folio={folio.id}, ramo={folio.ramo}, prima={folio.monto_prima}")
        
        signals = {
            "missing_docs": [doc.name for doc in folio.documents if doc.required and not doc.uploaded],
            "ramo": folio.ramo,
            "requiere_reaseguro": folio.requiere_reaseguro,
        }
        logger.debug(f"fetch_tramite: Extracted signals={signals}")
        return {"folio": folio, "signals": signals}

    def enrich_context(state: AnalyzerState) -> dict[str, Any]:
        logger.info("enrich_context: Enriching signals with additional context")
        signals = dict(state.signals)
        if state.folio and state.folio.catalog_line:
            signals["catalog_line"] = state.folio.catalog_line
            logger.debug(f"enrich_context: Added catalog_line={state.folio.catalog_line}")
        if state.folio and state.folio.estatus:
            signals["estatus"] = state.folio.estatus
            logger.debug(f"enrich_context: Added estatus={state.folio.estatus}")
        logger.debug(f"enrich_context: Final signals={signals}")
        return {"signals": signals}

    def score_risk(state: AnalyzerState) -> dict[str, Any]:
        assert state.folio, "Folio data missing before scoring"
        logger.info(f"score_risk: Calculating risk for folio={state.folio.id}")
        
        assessment = heuristic_score(state.folio, signals=state.signals)
        logger.debug(f"score_risk: Heuristic baseline score={assessment.score:.2f}, level={assessment.level}")
        
        delta = 0.0
        rationale = assessment.rationale
        recommendations = list(assessment.recommendations)

        if llm is not None:
            logger.debug("score_risk: Calling LLM for adjustment")
            llm_payload = {
                "folio": state.folio.model_dump(),
                "signals": state.signals,
                "baseline": assessment.model_dump(),
            }
            llm_chain = prompt | llm | StrOutputParser()
            raw = llm_chain.invoke(llm_payload)
            logger.debug(f"score_risk: LLM raw response: {raw[:200]}...")
            
            try:
                # Strip markdown code fences if present
                cleaned = raw.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]  # Remove ```json
                elif cleaned.startswith("```"):
                    cleaned = cleaned[3:]  # Remove ```
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]  # Remove trailing ```
                cleaned = cleaned.strip()
                
                parsed = json.loads(cleaned)
                delta = float(parsed.get("delta", 0.0))
                rationale = parsed.get("rationale", rationale)
                recommendations.extend(parsed.get("recommendations", []))
                logger.debug(f"score_risk: LLM delta={delta:.2f}, added {len(parsed.get('recommendations', []))} recommendations")
            except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as e:
                logger.warning(f"score_risk: LLM response parsing failed: {type(e).__name__}: {e}")
                recommendations.append("LLM no devolvió JSON válido; se conserva baseline")
        else:
            logger.debug("score_risk: No LLM configured, using heuristic score only")
            
        final_score = max(0.0, min(1.0, assessment.score + delta))
        level = "alto" if final_score >= 0.7 else "medio" if final_score >= 0.4 else "bajo"
        logger.info(f"score_risk: Final score={final_score:.2f}, level={level} (delta={delta:.2f})")
        
        risk = RiskAssessment(
            score=final_score,
            level=level,
            rationale=rationale,
            recommendations=recommendations,
        )
        return {
            "risk": {
                **risk.model_dump(),
                "baseline_score": assessment.score,
                "llm_delta": delta,
            }
        }

    def render_report(state: AnalyzerState) -> dict[str, Any]:
        assert state.folio and state.risk
        logger.info(f"render_report: Generating report for folio={state.folio.id}")
        
        risk = RiskAssessment.model_validate(state.risk)
        baseline_score = state.risk.get("baseline_score", risk.score)
        llm_delta = state.risk.get("llm_delta", 0.0)
        
        missing_docs = state.signals.get("missing_docs", [])
        logger.debug(f"render_report: Risk level={risk.level}, missing_docs={len(missing_docs)}, recommendations={len(risk.recommendations)}")
        
        # Build score breakdown
        score_breakdown = f"**{risk.level.upper()}** ({risk.score:.2f})"
        if llm_delta != 0.0:
            score_breakdown += f" [Heurístico: {baseline_score:.2f} + LLM: {llm_delta:+.2f}]"
        else:
            score_breakdown += f" [Heurístico: {baseline_score:.2f}]"
        
        report = [
            f"Folio **{state.folio.id}**",
            f"Nivel de riesgo: {score_breakdown}",
            f"Motivo: {risk.rationale}",
        ]
        if missing_docs:
            report.append(f"Documentos faltantes: {', '.join(missing_docs)}")
        if risk.recommendations:
            report.append("Recomendaciones:")
            for item in risk.recommendations:
                report.append(f"- {item}")
        
        logger.debug(f"render_report: Report has {len(report)} lines")
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

    logger.debug("build_app: LangGraph compiled with 4 nodes")
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
