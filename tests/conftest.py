"""Pytest configuration and fixtures for risk_analyzer tests."""

import os
from pathlib import Path

from dotenv import dotenv_values


# Load .env file and inject into os.environ BEFORE importing config
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    env_dict = dotenv_values(env_file)
    os.environ.update(env_dict)

# Now import config after environment is ready
from risk_analyzer.config import get_settings
get_settings.cache_clear()
