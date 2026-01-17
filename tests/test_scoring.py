from datetime import datetime

from risk_analyzer.schemas import TramiteDocument, TramiteFolio
from risk_analyzer.scoring import heuristic_score


def test_heuristic_score_caps_missing_docs():
    folio = TramiteFolio(
        folio="WFE-123",
        ramo="Daños",
        tipo_tramite="Emisión",
        monto_prima=1_500_000,
        requiere_reaseguro=True,
        es_urgente=True,
        catalog_line="Linea A",
        estatus="En revisión",
        updated_at=datetime.utcnow(),
        documents=[
            TramiteDocument(name="Contrato", required=True, uploaded=False),
            TramiteDocument(name="Carátula", required=True, uploaded=False),
            TramiteDocument(name="INE", required=False, uploaded=False),
        ],
    )

    assessment = heuristic_score(folio)

    assert assessment.level == "alto"
    assert 0.7 <= assessment.score <= 1.0
    assert "Contrato" in " ".join(assessment.rationale)
