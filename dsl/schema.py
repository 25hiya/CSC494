# dsl/schema.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class Environment(BaseModel):
    weather: str | None = None
    lighting: str | None = None
    road_condition: str | None = None
    additional_properties: Dict[str, Any] = Field(default_factory=dict)


class Actor(BaseModel):
    id: str
    type: str
    state: Dict[str, Any] = Field(default_factory=dict)


class RoadNetwork(BaseModel):
    road_type: str | None = None
    lanes: int | None = None
    traffic_controls: List[str] = Field(default_factory=list)
    additional_properties: Dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    description: str
    timestamp: str | None = None


class DSL(BaseModel):
    environment: Environment
    actors: List[Actor]
    road_network: RoadNetwork
    events: List[Event]
    metadata: Dict[str, Any] = Field(default_factory=dict)
