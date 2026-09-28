"""Schemas de validação de entrada (Pydantic v2)."""
from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config import ALL_REGIONS


class MonitorIn(BaseModel):
    """Payload aceito para criar um monitor (rota única, bulk, import)."""

    model_config = ConfigDict(extra="ignore")

    friendlyName: str = Field(..., min_length=1, description="Nome amigável do monitor")
    url: str = Field(..., min_length=1)
    interval: int = Field(default=300, ge=30, description="Intervalo de checagem em segundos")
    timeout: int = Field(default=30, ge=1, le=60)
    tagNames: List[str] = Field(default_factory=list)
    successHttpResponseCodes: List[str] = Field(default_factory=lambda: ["2xx", "3xx"])
    groupId: int = 0
    regions: List[str] = Field(default_factory=lambda: list(ALL_REGIONS))

    @field_validator("url")
    @classmethod
    def url_must_look_like_url(cls, v):
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url deve começar com http:// ou https://")
        return v

    @field_validator("regions")
    @classmethod
    def regions_must_be_valid(cls, v):
        invalid = [r for r in v if r not in ALL_REGIONS]
        if invalid:
            raise ValueError(f"Regiões inválidas: {invalid}. Use apenas: {ALL_REGIONS}")
        return v


class RegionsUpdateIn(BaseModel):
    """Body opcional da rota /set-regions-all."""

    regions: List[str] = Field(default_factory=lambda: list(ALL_REGIONS))
    dry_run: bool = False

    @field_validator("regions")
    @classmethod
    def regions_must_be_valid(cls, v):
        invalid = [r for r in v if r not in ALL_REGIONS]
        if invalid:
            raise ValueError(f"Regiões inválidas: {invalid}. Use apenas: {ALL_REGIONS}")
        return v
