from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.models import DisasterArea
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import DisasterAreaPropertiesCreate, MultiPolygon, Polygon
from app.tests.utils.utils import random_lower_string, random_coordinate


def square_around_coordinate_with_padding(
        c: List[float],
        p: float
) -> List[List[List[float]]]:
    return [[
        [c[0] - p, c[1] - p],
        [c[0] + p, c[1] - p],
        [c[0] + p, c[1] + p],
        [c[0] - p, c[1] + p],
        [c[0] - p, c[1] - p]]
    ]


def create_new_polygon(
        c: List[float] = None,
        f: float = 0.0001,
) -> Polygon:
    if c is None:
        c = random_coordinate(-10, 10)
    x = 1 * f
    return Polygon(
        coordinates=square_around_coordinate_with_padding(c, x)
    )


def create_new_multi_polygon(
        c: List[float] = None,
        f: float = 0.0001
) -> MultiPolygon:
    if c is None:
        c = random_coordinate(-10, 10)
    x = 1 * f
    return MultiPolygon(
        coordinates=[square_around_coordinate_with_padding(c, x),
                     square_around_coordinate_with_padding([n + 3 * x for n in c], x)]
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
        info: str = None,
        multi: bool = False

) -> DisasterArea:
    if c is None:
        c = random_coordinate(-10, 10)
    if name is None:
        name = random_lower_string(8)
    if info is None:
        info = random_lower_string(16)
    d_area = DisasterAreaCreate(
        geometry=create_new_multi_polygon(c, f) if multi else create_new_polygon(c, f),
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
