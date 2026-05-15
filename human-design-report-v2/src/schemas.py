from typing import Dict, List, Optional
from pydantic import BaseModel, Field

PLANETS = [
    "Sun", "Earth", "Moon", "North Node", "South Node", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
]


class ChartData(BaseModel):
    type: Optional[str] = None
    strategy: Optional[str] = None
    authority: Optional[str] = None
    profile: Optional[str] = None
    definition: Optional[str] = None
    incarnation_cross: Optional[str] = None
    personality: Dict[str, Optional[str]] = Field(default_factory=dict)
    design: Dict[str, Optional[str]] = Field(default_factory=dict)
    channels: List[str] = Field(default_factory=list)
    centers: Dict[str, Optional[str]] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
