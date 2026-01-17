"""Configuration helpers for the risk analyzer."""

from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime configuration derived from environment variables."""

    joget_base_url: str = Field(alias="JOGET_BASE_URL")
    joget_api_key: str = Field(alias="JOGET_API_KEY")
    joget_app_id: str = Field(alias="JOGET_APP_ID")
    joget_tramite_form_id: str = Field(alias="JOGET_TRAMITE_FORM_ID")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")

    class Config:
        populate_by_name = True
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process."""

    return Settings()  # pydantic reads from environment automatically
