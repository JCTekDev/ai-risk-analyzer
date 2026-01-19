import logging
from datetime import datetime

from risk_analyzer.schemas import TramiteDocument, TramiteFolio
from risk_analyzer.scoring import heuristic_score


logger = logging.getLogger(__name__)


def test_heuristic_score_caps_missing_docs():
    logger.info("Starting test_heuristic_score_caps_missing_docs")
    
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
    logger.debug(f"Created folio={folio.folio_id} ramo={folio.ramo} prima={folio.monto_prima}")

    assessment = heuristic_score(folio)
    logger.info(f"Assessment complete score={assessment.score:.2f} level={assessment.level}")

    logger.debug(f"Asserting level={assessment.level} == 'alto'")
    assert assessment.level == "alto"
    
    logger.debug(f"Asserting score {assessment.score} in range [0.7, 1.0]")
    assert 0.7 <= assessment.score <= 1.0
    
    logger.debug(f"Asserting '2 docs faltantes' in rationale")
    assert "2 docs faltantes" in assessment.rationale
    
    logger.debug(f"Asserting recommendations contains document solicitation")
    assert any("documentos faltantes" in rec.lower() for rec in assessment.recommendations)
    
    logger.info("test_heuristic_score_caps_missing_docs PASSED")
