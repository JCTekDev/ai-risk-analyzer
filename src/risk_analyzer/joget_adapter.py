"""Joget DX REST client used by the analyzer."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .config import get_settings
from .schemas import TramiteDocument, TramiteFolio


logger = logging.getLogger(__name__)


class JogetError(RuntimeError):
    """Raised when Joget DX responds with an unexpected payload."""


class JogetClient:
    """Thin wrapper around Joget DX JSON API."""

    def __init__(self, *, base_url: str | None = None, username: str | None = None, password: str | None = None):
        settings = get_settings()
        self._base_url = base_url or settings.joget_base_url.rstrip("/")
        self._username = username or settings.joget_username
        self._password = password or settings.joget_password
        self._session = httpx.Client(timeout=30.0)  # Increased timeout to 30s

    def _auth(self) -> tuple[str, str]:
        return (self._username, self._password)

    def get_form_data(self, app_id: str, form_id: str, primary_key: str) -> dict[str, Any]:
        """Fetch form data using Joget's JSON API."""

        url = f"{self._base_url}/web/json/data/form/load/{app_id}/{form_id}/{primary_key}"
        logger.debug(f"Joget GET: {url} (user={self._username})")
        
        try:
            response = self._session.get(url, auth=self._auth())
            logger.debug(f"Joget response: status={response.status_code}")
        except httpx.ReadError as e:
            logger.error(f"Joget connection error: {e}")
            raise JogetError(f"Failed to connect to Joget at {url}: {e}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Joget timeout: {e}")
            raise JogetError(f"Joget request timed out at {url}: {e}") from e
        
        if response.status_code >= 400:
            logger.error(f"Joget HTTP error {response.status_code}: {response.text[:200]}")
            raise JogetError(f"Joget returned {response.status_code}: {response.text}")
        try:
            payload = response.json()
            logger.debug(f"Joget returned {len(payload)} fields")
        except json.JSONDecodeError as exc:
            logger.error(f"Joget returned invalid JSON: {response.text[:200]}")
            raise JogetError("Joget response is not valid JSON") from exc
        return payload

    def fetch_tramite(self, folio_id: str) -> TramiteFolio:
        """Hydrate a `TramiteFolio` model from Joget form data."""

        settings = get_settings()
        raw = self.get_form_data(settings.joget_app_id, settings.joget_tramite_form_id, folio_id)
        
        # Parse documents: Joget returns it as a JSON string
        documents_raw = raw.get("documents", [])
        if isinstance(documents_raw, str):
            try:
                documents_raw = json.loads(documents_raw)
            except (json.JSONDecodeError, TypeError):
                documents_raw = []
        
        documents = [
            TramiteDocument(
                name=doc.get("name", "unknown"),
                required=self._parse_checkbox(doc.get("required")),
                uploaded=self._parse_checkbox(doc.get("uploaded")),
            )
            for doc in documents_raw if isinstance(doc, dict)
        ]
        
        # Prepare data dict with fallback: if 'folio' field is missing, map 'id' to 'folio'
        # This handles the case where the Joget form removed the 'folio' field
        data = {
            **raw,
            "documents": documents,
            "requiere_reaseguro": self._parse_checkbox(raw.get("requiere_reaseguro")),
            "es_urgente": self._parse_checkbox(raw.get("es_urgente")),
        }
        
        # If folio is not in data but id is, use id as the folio identifier
        if "folio" not in data and "id" in data:
            data["folio"] = data["id"]
            logger.debug(f"Mapped 'id' field to 'folio' identifier: {data['folio']}")
        
        return TramiteFolio.model_validate(data)

    @staticmethod
    def _parse_checkbox(value: Any) -> bool:
        """Convert Joget checkbox value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("on", "true", "1", "yes")
        return False


    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "JogetClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()
