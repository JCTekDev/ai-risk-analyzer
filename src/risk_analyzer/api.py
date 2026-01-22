"""FastAPI REST API for Risk Analyzer."""
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from langchain_openai import ChatOpenAI

from .config import get_settings
from .graph import build_app
from .schemas import AnalyzerState

logger = logging.getLogger(__name__)

# Global app instance (initialized at startup)
_graph_app = None
_llm = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - initialize resources at startup."""
    global _graph_app, _llm
    
    # Load environment variables
    env_file = os.getenv("ENV_FILE", ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        logger.info(f"Loaded environment from {env_file}")
    
    # Initialize LLM
    settings = get_settings()
    _llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )
    logger.info(f"Initialized ChatOpenAI with model={settings.llm_model}, temperature={settings.llm_temperature}")
    
    # Build LangGraph application
    _graph_app = build_app(llm=_llm)
    logger.info("LangGraph application initialized")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down API")


app = FastAPI(
    title="Risk Analyzer API",
    description="API for analyzing insurance workflow risk using Joget data and LLM",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "risk-analyzer"}


@app.post("/analyze/{id}")
async def analyze_risk(id: str) -> Dict[str, Any]:
    """
    Analyze risk for a given folio ID.
    
    Args:
        id: The primary key/folio ID from Joget
        
    Returns:
        JSON with id, folio data, signals, risk assessment (with baseline_score and llm_delta), and markdown report
    """
    global _graph_app, _llm
    
    # Initialize on first request if not already initialized (for TestClient compatibility)
    if _graph_app is None:
        logger.info("Lazy initialization on first request")
        env_file = os.getenv("ENV_FILE", ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file)
        
        settings = get_settings()
        _llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )
        _graph_app = build_app(llm=_llm)
    
    logger.info(f"Analyzing risk for id={id}")
    
    try:
        # Create initial state
        initial_state = AnalyzerState(id=id)
        
        # Invoke the graph
        result = _graph_app.invoke(initial_state)
        
        # Convert Pydantic model to dict for JSON serialization
        folio_dict = result["folio"].model_dump() if result.get("folio") else None
        
        # Build response
        response = {
            "id": result.get("id"),
            "folio": folio_dict,
            "signals": result.get("signals", {}),
            "risk": result.get("risk", {}),
            "report": result.get("report"),
        }
        
        logger.info(f"Analysis complete for id={id}, risk_level={result.get('risk', {}).get('level')}")
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing id={id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Risk Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze/{id}",
        },
    }
