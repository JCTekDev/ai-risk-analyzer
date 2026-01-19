"""Configuration helpers for the risk analyzer."""

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    """Runtime configuration derived from environment variables."""

    model_config = ConfigDict(populate_by_name=True, case_sensitive=False)

    joget_base_url: str = Field(alias="JOGET_BASE_URL")
    joget_username: str = Field(alias="JOGET_USERNAME")
    joget_password: str = Field(alias="JOGET_PASSWORD")
    joget_app_id: str = Field(alias="JOGET_APP_ID")
    joget_tramite_form_id: str = Field(alias="JOGET_TRAMITE_FORM_ID")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.0, alias="LLM_TEMPERATURE")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process from os.environ."""

    return Settings.model_validate(os.environ)
