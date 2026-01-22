"""CLI entry point for running the analyzer."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from .config import get_settings
from .graph import build_app
from .schemas import AnalyzerState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangGraph Joget risk analyzer")
    parser.add_argument("--id", required=True, help="Trámite folio identifier")
    parser.add_argument("--json", action="store_true", help="Print JSON payload instead of Markdown")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging")
    parser.add_argument(
        "--env-file",
        default=Path(".env"),
        help="Path to .env file with Joget/LLM credentials",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # Configure logging based on --debug flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)8s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting risk analyzer for id={args.id}")
    if args.debug:
        logger.debug("Debug mode enabled")
    
    load_dotenv(args.env_file)

    settings = get_settings()
    logger.debug(f"Loaded settings: base_url={settings.joget_base_url}, app_id={settings.joget_app_id}")
    
    llm = ChatOpenAI(model=settings.llm_model, temperature=settings.llm_temperature)
    logger.debug(f"Initialized LLM: {settings.llm_model} (temperature={settings.llm_temperature})")
    
    app = build_app(llm=llm)
    logger.debug("Built LangGraph app")
    
    result = app.invoke(AnalyzerState(id=args.id))
    logger.info("Analysis complete")

    if args.json:
        # Convert Pydantic models to dicts for JSON serialization
        json_result = {
            "id": result.get("id"),
            "folio": result["folio"].model_dump() if result.get("folio") else None,
            "signals": result.get("signals"),
            "risk": result.get("risk"),
            "report": result.get("report"),
        }
        print(json.dumps(json_result, indent=2, ensure_ascii=False))
    else:
        print(result.get("report"))


if __name__ == "__main__":
    main()
