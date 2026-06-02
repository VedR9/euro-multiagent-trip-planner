from pydantic import BaseModel, Field
from typing import List, Optional

class TravelProfile(BaseModel):
    destinations: List[str] = Field(default_factory=list)
    budget: float = 0.0
    duration_days: int = 0
    preferences: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

class Activity(BaseModel):
    name: str
    location: str
    estimated_cost: float
    duration_hours: float
    description: str

class Accommodation(BaseModel):
    name: str
    neighborhood: str
    cost_per_night: float
    total_cost: float
    description: str

class SharedState(BaseModel):
    original_prompt: str = ""
    profile: Optional[TravelProfile] = None
    candidate_activities: List[Activity] = Field(default_factory=list)
    accommodations: List[Accommodation] = Field(default_factory=list)
    total_estimated_cost: float = 0.0
    final_itinerary: str = ""
    status: str = "initialized"
