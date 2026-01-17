"""CLI entry point for running the analyzer."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .graph import build_app
from .schemas import AnalyzerState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangGraph Joget risk analyzer")
    parser.add_argument("--folio-id", required=True, help="Trámite folio identifier")
    parser.add_argument("--json", action="store_true", help="Print JSON payload instead of Markdown")
    parser.add_argument(
        "--env-file",
        default=Path(".env"),
        help="Path to .env file with Joget/LLM credentials",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(args.env_file)

    app = build_app()
    result = app.invoke(AnalyzerState(folio_id=args.folio_id))

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("report"))


if __name__ == "__main__":
    main()
