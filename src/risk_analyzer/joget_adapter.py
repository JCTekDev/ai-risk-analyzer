"""Joget DX REST client used by the analyzer."""

from __future__ import annotations

import json
from typing import Any

import httpx

from .config import get_settings
from .schemas import TramiteDocument, TramiteFolio


class JogetError(RuntimeError):
    """Raised when Joget DX responds with an unexpected payload."""


class JogetClient:
    """Thin wrapper around Joget DX JSON API."""

    def __init__(self, *, base_url: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self._base_url = base_url or settings.joget_base_url.rstrip("/")
        self._api_key = api_key or settings.joget_api_key
        self._session = httpx.Client(timeout=10.0)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def get_form_data(self, form_id: str, primary_key: str) -> dict[str, Any]:
        """Fetch form data using Joget's JSON API."""

        url = f"{self._base_url}/api/json/form/{form_id}"
        params = {"primaryKeyValue": primary_key}
        response = self._session.get(url, params=params, headers=self._headers())
        if response.status_code >= 400:
            raise JogetError(f"Joget returned {response.status_code}: {response.text}")
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise JogetError("Joget response is not valid JSON") from exc
        return payload

    def fetch_tramite(self, folio_id: str) -> TramiteFolio:
        """Hydrate a `TramiteFolio` model from Joget form data."""

        settings = get_settings()
        raw = self.get_form_data(settings.joget_tramite_form_id, folio_id)
        documents = [
            TramiteDocument(
                name=doc.get("name", "unknown"),
                required=bool(doc.get("required")),
                uploaded=bool(doc.get("uploaded")),
            )
            for doc in raw.get("documents", [])
        ]
        return TramiteFolio.model_validate({**raw, "documents": documents})

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "JogetClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()
