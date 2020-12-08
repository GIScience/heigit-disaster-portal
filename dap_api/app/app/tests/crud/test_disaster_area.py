import json

from geojson_pydantic.geometries import Polygon
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import crud
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import DisasterAreaPropertiesCreate, DisasterAreaUpdate
from app.tests.utils.disaster_areas import create_new_disaster_area, create_new_polygon, create_new_properties
from app.tests.utils.utils import random_lower_string


def test_create_disaster_area(db: Session) -> None:
    d_area_obj = DisasterAreaCreate(
        geometry=Polygon(
            coordinates=[[[1, 2], [3, 4], [6, 5], [1, 2]]]
        ),
        properties=DisasterAreaPropertiesCreate(
            name=random_lower_string(8),
            d_type_id=1,
            provider_id=1
        )
    )
    disaster_area = crud.disaster_area.create(db, obj_in=d_area_obj)
    assert disaster_area.name == d_area_obj.properties.name
    assert disaster_area.description == d_area_obj.properties.description
    assert disaster_area.d_type_id == d_area_obj.properties.d_type_id
    assert disaster_area.id


def test_get_disaster_area_by_id(db: Session) -> None:
    d_area = create_new_disaster_area(db, (2, 2))
    d_area_get = crud.disaster_area.get(db, id=d_area.id)
    assert d_area.name == d_area_get.name


def test_get_disaster_area_by_name(db: Session) -> None:
    d_area = create_new_disaster_area(db, (2, 2))
    d_area_get = crud.disaster_area.get_by_name(db, name=d_area.name)
    assert d_area.name == d_area_get.name


def test_get_disaster_areas(db: Session) -> None:
    d_area1 = create_new_disaster_area(db, (2, 2))
    d_area2 = create_new_disaster_area(db, (-2, 2))
    d_areas = crud.disaster_area.get_multi(db)
    assert d_area1 in d_areas
    assert d_area2 in d_areas
    for area in [dict({"name": x.name, "a_id": x.id}) for x in d_areas]:
        assert area.get("name")
        assert area.get("a_id")


def test_get_disaster_area_as_feature(db: Session) -> None:
    d_area = create_new_disaster_area(db, (2, 2))
    d_area2 = crud.disaster_area.get_as_feature(db, d_area.id)
    assert d_area.id == d_area2.id
    assert d_area.name == d_area2.properties.name
    assert d_area2.bbox
    # TODO: write better tests
    # in d_area the geometry is still stored in EWKB format. After conversion to geojson values are still integer
    # that's why we pass it to the Polygon model again before getting the json value back.
    assert d_area2.geometry == Polygon(**json.loads(db.execute(d_area.geom.st_asgeojson()).scalar()))


def test_get_disaster_areas_by_bbox(db: Session) -> None:
    d_area1 = create_new_disaster_area(db, (2, 2))
    d_area2 = create_new_disaster_area(db, (-2, 2))
    d_area3 = create_new_disaster_area(db, (1, 2))
    d_areas = crud.disaster_area.get_multi(db, bbox=(0., 0., 2., 2.))
    assert d_area1 in d_areas
    assert d_area2 not in d_areas
    assert d_area3 in d_areas


def test_update_disaster_area_properties(db: Session) -> None:
    d_area = create_new_disaster_area(db, (2, 2), f=2)
    d_area_update = dict({"properties": {
        "description": "Updated description"
    }})
    d_area2 = crud.disaster_area.update(db, db_obj=d_area, obj_in=d_area_update)
    assert d_area2 == d_area
    assert d_area2.description == d_area_update["properties"]["description"]


def test_update_disaster_area_geometry(db: Session) -> None:
    d_area = create_new_disaster_area(db, (2, 2), f=2)
    geom = create_new_polygon((-1, -1))
    d_area_update = DisasterAreaUpdate(
        geometry=geom,
        properties=create_new_properties(
            d_id=d_area.d_type_id,
            p_id=d_area.provider_id,
            info=d_area.description
        )
    )
    d_area2 = crud.disaster_area.update(db, db_obj=d_area, obj_in=d_area_update)
    assert d_area2 == d_area
    assert d_area2.geom == db.execute(func.ST_GeomFromGeoJSON(geom.json())).scalar()


def test_remove_disaster_area(db: Session) -> None:
    d_area = create_new_disaster_area(db, (-1, -4), f=2)
    d_area_2 = crud.disaster_area.remove(db, id=d_area.id)
    no_d_area = crud.provider.get(db, id=d_area_2.id)
    assert d_area == d_area_2
    assert not no_d_area