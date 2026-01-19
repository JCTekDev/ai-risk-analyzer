import logging

import pytest

from risk_analyzer.joget_adapter import JogetClient, JogetError
from risk_analyzer.schemas import TramiteFolio
from risk_analyzer.config import get_settings


logger = logging.getLogger(__name__)


@pytest.mark.integration
def test_joget_client_fetch_tramite_real():
    """Test real REST call to Joget Form API (integration test)."""
    logger.info("Starting test_joget_client_fetch_tramite_real - LIVE JOGET CALL")

    settings = get_settings()
    logger.debug(f"Using Joget at {settings.joget_base_url} with app {settings.joget_app_id}")

    client = JogetClient()
    logger.debug("Created JogetClient with credentials from .env")

    try:
        folio = client.fetch_tramite("34666095-2358-4109-a63d-abaf8c215e82")
        logger.info(f"✓ Successfully fetched folio={folio.folio_id} ramo={folio.ramo} prima={folio.monto_prima}")

        # Validate the result is a TramiteFolio instance
        assert isinstance(folio, TramiteFolio)
        logger.debug("Folio is TramiteFolio instance")

        # Validate core fields
        assert folio.folio_id == "WFE-123"
        logger.debug(f"✓ folio_id: {folio.folio_id}")

        assert folio.ramo in ["Da&ntilde;os", "Vida", "Da&ntilde;os y Vida"]
        logger.debug(f"✓ ramo: {folio.ramo}")

        assert folio.monto_prima > 0
        logger.debug(f"✓ monto_prima: {folio.monto_prima}")

        assert isinstance(folio.requiere_reaseguro, bool)
        logger.debug(f"✓ requiere_reaseguro: {folio.requiere_reaseguro}")

        # Validate documents list
        assert isinstance(folio.documents, list)
        logger.info(f"✓ Documents count: {len(folio.documents)}")
        for i, doc in enumerate(folio.documents):
            logger.debug(f"  Doc {i}: name={doc.name}, required={doc.required}, uploaded={doc.uploaded}")

        logger.info("✓ test_joget_client_fetch_tramite_real PASSED")

    except JogetError as e:
        logger.error(f"✗ JogetError: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Unexpected error: {type(e).__name__}: {e}")
        raise


@pytest.mark.integration
@pytest.mark.skip(reason="Run only when Joget is unavailable - tests error handling")
def test_joget_client_connection_error():
    """Test error handling when Joget is unreachable."""
    logger.info("Starting test_joget_client_connection_error")

    client = JogetClient(base_url="http://localhost:9999/jw")  # Invalid port
    logger.debug("Created client pointing to invalid Joget URL")

    try:
        client.fetch_tramite("34666095-2358-4109-a63d-abaf8c215e82")
        pytest.fail("Should have raised an error")
    except Exception as e:
        logger.info(f"✓ Connection error caught as expected: {type(e).__name__}")


@pytest.fixture
def joget_response_payload():
    """Mock JSON response from Joget Form API for non-integration tests."""
    return {
        "folio": "WFE-123",
        "ramo": "Daños",
        "tipo_tramite": "Emisión",
        "monto_prima": "1500000",
        "requiere_reaseguro": True,
        "es_urgente": True,
        "catalog_line": "Línea A",
        "estatus": "En revisión",
        "updated_at": "2026-01-19T10:30:00",
        "documents": [
            {"name": "Contrato", "required": True, "uploaded": False},
            {"name": "Carátula", "required": True, "uploaded": False},
            {"name": "INE", "required": False, "uploaded": False},
        ],
    }


def test_tramite_folio_model_validation(joget_response_payload):
    """Test TramiteFolio model parsing without Joget (unit test)."""
    logger.info("Starting test_tramite_folio_model_validation")

    folio = TramiteFolio.model_validate(joget_response_payload)
    logger.info(f"✓ TramiteFolio model validates from payload")

    assert folio.folio_id == "WFE-123"
    assert folio.monto_prima == 1500000.0
    assert isinstance(folio.monto_prima, float)
    logger.debug("✓ Numeric conversion working (monto_prima string->float)")

    assert len(folio.documents) == 3
    logger.info("✓ test_tramite_folio_model_validation PASSED")
