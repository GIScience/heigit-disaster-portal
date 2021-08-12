import json

import pytest
from sqlalchemy.orm import Session

from app import crud
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import MultiPolygon
from app.tests.utils.disaster_areas import create_new_disaster_area
from app.tests.utils.utils import random_lower_string


def test_create_disaster_area_multi(db: Session) -> None:
    d_area_obj = DisasterAreaCreate(
        geometry={
            "type": "MultiPolygon",
            "coordinates": [[[[2, 2], [2, 4], [4, 2], [2, 2]]], [[[4, 4], [3.5, 3.5], [4, 3], [4, 4]]]]
        },
        properties={
            "name": random_lower_string(8),
            "d_type_id": 1,
            "provider_id": 1
        }
    )
    disaster_area = crud.disaster_area.create(db, obj_in=d_area_obj)
    assert disaster_area.name == d_area_obj.properties.name
    assert disaster_area.description == d_area_obj.properties.description
    assert disaster_area.d_type_id == d_area_obj.properties.d_type_id
    assert disaster_area.id


def test_get_disaster_area_multi(db: Session) -> None:
    d_area = create_new_disaster_area(db, [2.4321234124, 2.4321143124], multi=True)
    d_area2 = crud.disaster_area.get_as_feature(db, d_area.id)
    assert d_area.id == d_area2.id
    assert d_area.name == d_area2.properties.name
    assert d_area2.bbox
    # TODO: write better tests
    # in d_area the geometry is still stored in EWKB format. After conversion to geojson values are still integer
    # that's why we pass it to the Polygon model again before getting the json value back.
    assert d_area2.geometry == MultiPolygon(**json.loads(db.execute(d_area.geom.st_asgeojson(7)).scalar()))
