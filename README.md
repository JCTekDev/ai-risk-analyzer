# Risk Analyzer

LangGraph-based assistant that reads Joget DX 8.0.10 Trámite Folio data, applies deterministic risk heuristics, and produces analyst-friendly guidance.

## Features
- Thin Joget REST adapter that hydrates folio metadata into typed models.
- Deterministic rule engine plus LLM adjustment for explainable scoring.
- LangGraph state machine with fetch → enrich → score → report stages.
- Portable CLI entry point and pytest-covered heuristics.

## Getting Started
1. **Install dependencies**
   ```bash
   cd risk-analyzer
   python3 -m venv .venv && source .venv/bin/activate
   uv pip install -e .[dev]
   ```
2. **Configure environment**
   Copy `.env.example` to `.env` and set:
   - `JOGET_BASE_URL` (e.g., `http://localhost:8080/jw`)
   - `JOGET_USERNAME` (e.g., `admin`)
   - `JOGET_PASSWORD` (e.g., `admin`)
   - `JOGET_APP_ID` (e.g., `insurancePoliciesWorkflow`)
   - `JOGET_TRAMITE_FORM_ID` (e.g., `insurance_policies`)
   - `OPENAI_API_KEY` (or any LangChain-compatible LLM provider)

3. **Sample Joget form data**
   The analyzer expects Joget forms with these fields:
   ```json
   {
     "folio": "WFE-123",
     "ramo": "Daños",
     "tipo_tramite": "Emisión",
     "monto_prima": "1500000",
     "requiere_reaseguro": "on",
     "es_urgente": "on",
     "catalog_line": "Línea A",
     "estatus": "En revisión",
     "documents": "[{\"name\":\"Contrato\",\"required\":true,\"uploaded\":false},{\"name\":\"Carátula\",\"required\":true,\"uploaded\":false}]"
   }
   ```
   - Checkbox fields return `"on"` when checked (auto-converted to `True`)
   - Decimal fields return strings (auto-converted to `float`)
   - Documents grid returns as a JSON string array

4. **Run analyzer**
   ```bash
   # Basic usage
   python -m risk_analyzer.main --folio-id 34666095-2358-4109-a63d-abaf8c215e82
   
   # With debug logging
   python -m risk_analyzer.main --folio-id 34666095-2358-4109-a63d-abaf8c215e82 --debug
   
   # Output as JSON instead of Markdown
   python -m risk_analyzer.main --folio-id 34666095-2358-4109-a63d-abaf8c215e82 --json
   ```
   
   **Command line options:**
   - `--folio-id`: Trámite folio identifier (required)
   - `--debug`: Enable DEBUG level logging to trace execution flow
   - `--json`: Output raw JSON instead of Markdown report
   - `--env-file`: Path to .env file (default: `.env`)

5. **Run tests**
   ```bash
   pytest
   ```

## Architecture
```
StateGraph
 ├─ fetch_tramite        → pulls Joget data
 ├─ enrich_context       → resolves catalogs, SLAs
 ├─ score_risk           → merges heuristics + LLM delta
 └─ render_report        → composes JSON + Markdown output
```

Each node writes to a shared `AnalyzerState`, ensuring reproducible and testable transitions.

## Notes
- The adapter uses Joget's `/web/json/data/form/load/{app_id}/{form_id}/{primary_key}` endpoint with HTTP Basic Auth.
- Joget checkbox fields return `"on"` when checked; the adapter auto-converts to `True`.
- The `documents` field is returned as a JSON string from the form grid; the adapter parses it into typed `TramiteDocument` objects.
- Risk heuristics live in `risk_analyzer.scoring` for focused unit tests.
- `langgraph` execution stays synchronous for simplicity, but you can wrap nodes with async `httpx.AsyncClient` if throughput becomes critical.
