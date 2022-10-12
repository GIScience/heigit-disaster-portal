from sqlite3.dbapi2 import Timestamp
from typing import Optional, List, Dict, Any

from geoalchemy2 import func
from geojson_pydantic.geometries import _GeometryBase
from pydantic import BaseModel, validator, root_validator


def check_polygon_rings(rings):
    # TODO: output element of error by using if list comprehensions if not too slow
    if any([len(c) < 4 for c in rings]):
        raise ValueError("Linear rings must have four or more coordinates")
    if any([c[-1] != c[0] for c in rings]):
        raise ValueError("Linear rings must have the same start and end coordinates")
    if any([any([len(c) != 2 for c in ring]) for ring in rings]):
        raise ValueError("Coordinates must have exactly two values")
    if not all([all([-180 <= c[0] <= 180 for c in ring]) for ring in rings]):
        raise ValueError("Longitude needs to be in range +-180")
    if not all([all([-90 <= c[1] <= 90 for c in ring]) for ring in rings]):
        raise ValueError("Latitude needs to be in range +-90")


# Adjusted from implementation at geojson_pydantic.geometries:
# The float | int type of the Coordinate generates an invalid swagger specification,
# which can't be rendered in the interactive documentation.
# Also defining a custom Coordinate class using a root validator (like BBoxModel) is not playing
# well with returning the coordinates as a normal list object.
# Therefore all validations for coordinates are done directly in the Polygon class below
class Polygon(_GeometryBase):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]

    @validator("coordinates")
    def check_coordinates(cls, rings):
        check_polygon_rings(rings)
        return rings


class MultiPolygon(_GeometryBase):
    type: str = "MultiPolygon"
    coordinates: List[List[List[List[float]]]]

    @validator("coordinates")
    def check_coordinates(cls, polygons):
        for rings in polygons:
            check_polygon_rings(rings)
        return polygons


class FeatureBase(BaseModel):
    type: str = "Feature"
    geometry: Polygon | MultiPolygon
    properties: Optional[Dict[Any, Any]]

    class Config:
        use_enum_values = True

    @validator("geometry", pre=True, always=True)
    def set_geometry(cls, v):
        if hasattr(v, "__geo_interface__"):
            return v.__geo_interface__
        return v


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
class DisasterAreaBase(FeatureBase):
    geometry: Optional[Polygon | MultiPolygon]
    properties: Optional[DisasterAreaPropertiesBase]


class DisasterAreaPropertiesCreate(DisasterAreaPropertiesBase):
    name: str
    provider_id: int
    d_type_id: int


# Properties to receive via API on creation
class DisasterAreaCreate(DisasterAreaBase):
    type: str = "Feature"
    geometry: Polygon | MultiPolygon
    properties: DisasterAreaPropertiesCreate

    @validator("geometry")
    def check_validity(cls, geometry):
        from app.db.session import SessionLocal
        db = SessionLocal()
        geom = func.ST_GeomFromGeoJSON(geometry.json())
        valid_check = db.query(func.ST_IsValidReason(geom)).first()[0]
        db.close()
        if valid_check != "Valid Geometry":
            raise ValueError(f"Geometry not valid: {valid_check}")
        return geometry


class DisasterAreaPropertiesCreateOut(DisasterAreaPropertiesCreate):
    created: Timestamp
    area: float


# Properties to return via API on creation
class DisasterAreaCreateOut(DisasterAreaCreate):
    properties: DisasterAreaPropertiesCreateOut
    id: int
    bbox: BBoxModel


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
    bbox: BBoxModel


# Additional properties stored in DB
class DisasterAreaInDB(DisasterAreaInDBBase):
    pass


# Schema for feature collection response
class DisasterAreaCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[DisasterArea]
    bbox: BBoxModel
