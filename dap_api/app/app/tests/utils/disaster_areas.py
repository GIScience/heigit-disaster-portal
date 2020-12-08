from typing import Tuple

from geojson_pydantic.geometries import Polygon
from geojson_pydantic.utils import NumType
from sqlalchemy.orm import Session

from app import crud
from app.models import DisasterArea
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import DisasterAreaPropertiesCreate
from app.tests.utils.utils import random_lower_string


def create_new_polygon(
        c: Tuple[NumType, NumType],
        f: int = 1,
) -> Polygon:
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
        info: str = random_lower_string(16)
) -> DisasterAreaPropertiesCreate:
    return DisasterAreaPropertiesCreate(
        name=random_lower_string(8),
        d_type_id=d_id,
        provider_id=p_id,
        description=info
    )


def create_new_disaster_area(
        db: Session,
        c: Tuple[NumType, NumType],
        f: int = 1,
        p_id: int = 1,
        d_id: int = 1
) -> DisasterArea:
    d_area = DisasterAreaCreate(
        geometry=create_new_polygon(c, f),
        properties=DisasterAreaPropertiesCreate(
            name=random_lower_string(8),
            d_type_id=d_id,
            provider_id=p_id
        )
    )
    return crud.disaster_area.create(
        db=db,
        obj_in=d_area
    )
