from typing import List

from geojson_pydantic.geometries import Polygon
from sqlalchemy.orm import Session

from app import crud
from app.models import DisasterArea
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import DisasterAreaPropertiesCreate
from app.tests.utils.utils import random_lower_string, random_coordinate


def create_new_polygon(
        c: List[float] = None,
        f: float = 0.0001,
) -> Polygon:
    if c is None:
        c = random_coordinate(-10, 10)
    x = 1 * f
    return Polygon(
        coordinates=[[
            [c[0] - x, c[1] - x],
            [c[0] + x, c[1] - x],
            [c[0] + x, c[1] + x],
            [c[0] - x, c[1] + x],
            [c[0] - x, c[1] - x]
        ]]
    )


def create_new_properties(
        p_id: int = 1,
        d_id: int = 1,
        name: str = None,
        info: str = None
) -> DisasterAreaPropertiesCreate:
    if name is None:
        name = random_lower_string(8)
    if info is None:
        info = random_lower_string(16)
    return DisasterAreaPropertiesCreate(
        name=name,
        d_type_id=d_id,
        provider_id=p_id,
        description=info
    )


def create_new_disaster_area(
        db: Session,
        c: List[float] = None,
        f: float = 0.0001,
        name: str = None,
        p_id: int = 1,
        d_id: int = 1,
        info: str = None

) -> DisasterArea:
    if c is None:
        c = random_coordinate(-10, 10)
    if name is None:
        name = random_lower_string(8)
    if info is None:
        info = random_lower_string(16)
    d_area = DisasterAreaCreate(
        geometry=create_new_polygon(c, f),
        properties=DisasterAreaPropertiesCreate(
            name=name,
            d_type_id=d_id,
            provider_id=p_id,
            description=info
        )
    )
    return crud.disaster_area.create(
        db=db,
        obj_in=d_area
    )
