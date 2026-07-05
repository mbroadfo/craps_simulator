"""Request bodies for the Observatory API (Phase 2, Step 1).

House rules (including the D6 availability flags) pass through as a
plain dict — HouseRules is the single schema authority, exactly as the
event dataclasses are for the stream. table_id is constrained because
it becomes part of the recording filename.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlayerSpec(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    strategy: str


class CreateTableRequest(BaseModel):
    table_id: Optional[str] = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,40}$")
    players: List[PlayerSpec] = Field(min_length=1)
    house_rules: Optional[Dict[str, Any]] = None
    num_shooters: int = Field(default=10, ge=1)
    max_rolls: Optional[int] = Field(default=None, ge=1)
    roll_delay_ms: int = Field(default=0, ge=0)
    dice_seed: Optional[int] = None
    record: bool = True


class PaceRequest(BaseModel):
    roll_delay_ms: int = Field(ge=0)
