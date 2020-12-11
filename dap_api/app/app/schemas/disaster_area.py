from sqlite3.dbapi2 import Timestamp
from typing import Optional, List

from geoalchemy2 import func
from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon
from geojson_pydantic.utils import BBox
from pydantic import BaseModel, validator, root_validator


class BBoxModel(BaseModel):
    __root__: List[float]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]

    @root_validator(pre=True)
    def validate_len(cls, values):
        if len(values['__root__']) != 4:
            raise ValueError("bbox needs 4 values: west(lon), south(lat), east(lon), north(lat)")
        return values

    @root_validator(pre=True)
    def validate_coords(cls, values):
        if abs(values['__root__'][0]) > 180:
            raise ValueError("invalid west longitude")
        if abs(values['__root__'][1]) > 90:
            raise ValueError("invalid south latitude")
        if abs(values['__root__'][2]) > 180:
            raise ValueError("invalid east longitude")
        if abs(values['__root__'][3]) > 90:
            raise ValueError("invalid north latitude")
        return values


class DisasterAreaPropertiesBase(BaseModel):
    name: Optional[str] = None
    provider_id: Optional[int] = None
    d_type_id: Optional[int] = None
    ds_type_id: Optional[int] = None
    description: Optional[str] = None


# Shared properties
class DisasterAreaBase(Feature):
    geometry: Optional[Polygon]
    properties: Optional[DisasterAreaPropertiesBase]


class DisasterAreaPropertiesCreate(DisasterAreaPropertiesBase):
    name: str
    provider_id: int
    d_type_id: int


# Properties to receive via API on creation
class DisasterAreaCreate(DisasterAreaBase):
    type: str = "Feature"
    geometry: Polygon
    properties: DisasterAreaPropertiesCreate
    id: Optional[int] = None
    bbox: Optional[BBox] = None

    @validator("geometry")
    def check_validity(cls, geometry):
        from app.db.session import SessionLocal
        db = SessionLocal()
        geom = func.ST_GeomFromGeoJSON(geometry.json())
        valid_check = db.query(func.ST_IsValidReason(geom)).first()[0]
        if valid_check != "Valid Geometry":
            raise ValueError(f"Geometry not valid: {valid_check}")
        return geometry


class DisasterAreaPropertiesCreateOut(DisasterAreaPropertiesCreate):
    created: Timestamp
    area: float


# Properties to return via API on creation
class DisasterAreaCreateOut(DisasterAreaCreate):
    properties: DisasterAreaPropertiesCreateOut
    bbox: BBox
    pass


# Properties to receive via API on update
class DisasterAreaUpdate(DisasterAreaBase):
    pass


class DisasterAreaInDBBase(DisasterAreaBase):
    id: int

    class Config:
        orm_mode = True


# Additional properties to return via API
class DisasterArea(DisasterAreaInDBBase):
    properties: DisasterAreaPropertiesCreateOut


# Additional properties stored in DB
class DisasterAreaInDB(DisasterAreaInDBBase):
    pass


# Schema for feature collection response
class DisasterAreaCollection(FeatureCollection):
    features: List[DisasterArea]
