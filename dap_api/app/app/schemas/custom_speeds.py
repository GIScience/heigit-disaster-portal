from sqlite3.dbapi2 import Timestamp
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, validator, root_validator, Field


class CustomSpeedsPropertiesBase(BaseModel):
    name: str
    description: Optional[str] = None
    provider_id: Optional[int] = None


class RoadSpeeds(BaseModel):
    primary: Optional[int]
    primary_link: Optional[int]
    motorway: Optional[int]
    motorway_link: Optional[int]
    trunk: Optional[int]
    trunk_link: Optional[int]
    secondary: Optional[int]
    secondary_link: Optional[int]
    tertiary: Optional[int]
    tertiary_link: Optional[int]
    road: Optional[int]
    unclassified: Optional[int]
    residential: Optional[int]
    service: Optional[int]
    living_street: Optional[int]
    path: Optional[int]
    track: Optional[int]
    cycleway: Optional[int]
    footway: Optional[int]
    pedestrian: Optional[int]
    crossing: Optional[int]
    steps: Optional[int]
    construction: Optional[int]


class SurfaceSpeeds(BaseModel):
    paved: Optional[int]
    unpaved: Optional[int]
    asphalt: Optional[int]
    concrete: Optional[int]
    concrete_lanes: Optional[int] = Field(alias='concrete:lanes')
    concrete_plates: Optional[int] = Field(alias='concrete:plates')
    paving_stones: Optional[int]
    paving_stones_20: Optional[int] = Field(alias='paving_stones:20')
    paving_stones_30: Optional[int] = Field(alias='paving_stones:30')
    paving_stones_50: Optional[int] = Field(alias='paving_stones:50')
    paved_stones: Optional[int]
    cobblestone_flattened: Optional[int] = Field(alias='cobblestone:flattened')
    sett: Optional[int]
    cobblestone: Optional[int]
    metal: Optional[int]
    wood: Optional[int]
    compacted: Optional[int]
    pebblestone: Optional[int]
    fine_gravel: Optional[int]
    gravel: Optional[int]
    dirt: Optional[int]
    ground: Optional[int]
    earth: Optional[int]
    mud: Optional[int]
    ice: Optional[int]
    snow: Optional[int]
    sand: Optional[int]
    woodchips: Optional[int]
    grass: Optional[int]
    grass_paver: Optional[int]


class CustomSpeedsContent(BaseModel):
    unit: Optional[str] = "kmh"
    roadSpeeds: Optional[RoadSpeeds]
    surfaceSpeeds: Optional[SurfaceSpeeds]


# Shared properties
class CustomSpeeds(BaseModel):
    content: CustomSpeedsContent
    properties: Optional[CustomSpeedsPropertiesBase]


class CustomSpeedsProperties(CustomSpeedsPropertiesBase):
    name: str
    provider_id: int


# Properties to receive via API on creation
class CustomSpeedsCreate(CustomSpeeds):
    content: dict
    properties: CustomSpeedsProperties


class CustomSpeedsPropertiesOut(CustomSpeedsProperties):
    created: Timestamp


# Properties to return via API on creation
class CustomSpeedsCreateOut(CustomSpeedsCreate):
    properties: CustomSpeedsPropertiesOut
    id: int


# Properties to receive via API on update
class CustomSpeedsUpdate(CustomSpeeds):
    pass

