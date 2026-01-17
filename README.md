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
   - `JOGET_BASE_URL`
   - `JOGET_API_KEY`
   - `JOGET_APP_ID`
   - `JOGET_TRAMITE_FORM_ID`
   - `OPENAI_API_KEY` (or any LangChain-compatible LLM provider)
3. **Run analyzer**
   ```bash
   python -m risk_analyzer.main --folio-id WFE-TRAM-0001
   ```
4. **Run tests**
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
- The adapter assumes Joget API key authentication. Swap for OAuth/OIDC as needed.
- Risk heuristics live in `risk_analyzer.scoring` for focused unit tests.
- `langgraph` execution stays synchronous for simplicity, but you can wrap nodes with async `httpx.AsyncClient` if throughput becomes critical.
