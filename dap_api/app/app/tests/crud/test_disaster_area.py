import json
from datetime import datetime as dt

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import crud
from app.crud.crud_disaster_area import multi_to_single
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import DisasterAreaPropertiesCreate, DisasterAreaUpdate, Polygon, MultiPolygon
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
    d_area = create_new_disaster_area(db, [2, 2])
    d_area_get = crud.disaster_area.get(db, id=d_area.id)
    assert d_area.name == d_area_get.name


def test_get_disaster_area_by_name(db: Session) -> None:
    d_area = create_new_disaster_area(db, [2, 2])
    d_area_get = crud.disaster_area.get_by_name(db, name=d_area.name)
    assert d_area.name == d_area_get.name


def test_get_disaster_area_by_d_type(db: Session) -> None:
    d_area1 = create_new_disaster_area(db, [2, 2], d_id=3)
    d_area2 = create_new_disaster_area(db, [-2, 2], d_id=5)
    d_area3 = create_new_disaster_area(db, [1, 2], d_id=3)
    d_area4 = create_new_disaster_area(db, [-2, 2], d_id=4)

    areas_type_3 = crud.disaster_area.get_multi(db, d_type_id=3)
    assert all(x in areas_type_3 for x in [d_area1, d_area3])
    assert all(x not in areas_type_3 for x in [d_area2, d_area4])

    areas_type_5 = crud.disaster_area.get_multi(db, d_type_id=5)
    assert d_area2 in areas_type_5
    assert all(x not in areas_type_5 for x in [d_area1, d_area3, d_area4])

    areas_type_7 = crud.disaster_area.get_multi(db, d_type_id=7)
    assert all(x not in areas_type_7 for x in [d_area1, d_area2, d_area3, d_area4])
    assert areas_type_7 == []


def test_get_disaster_area_by_datetime(db: Session) -> None:
    t1 = dt.now()
    d_area1 = create_new_disaster_area(db)
    d_area2 = create_new_disaster_area(db)
    t2 = dt.now()
    d_area3 = create_new_disaster_area(db)
    d_area4 = create_new_disaster_area(db)
    t3 = dt.now()
    d_area5 = create_new_disaster_area(db)
    t4 = dt.now()

    one_exact_datetime = crud.disaster_area.get_multi(db, date_time=f"{d_area1.created}")
    assert len(one_exact_datetime) == 1
    assert one_exact_datetime[0] == d_area1

    t1_to_t2 = crud.disaster_area.get_multi(db, date_time=f"{t1}/{t2}")
    assert len(t1_to_t2) == 2
    assert d_area1 in t1_to_t2
    assert d_area2 in t1_to_t2

    before_t3 = crud.disaster_area.get_multi(db, date_time=f"/{t3}")
    before_t3_2 = crud.disaster_area.get_multi(db, date_time=f"../{t3}")
    assert before_t3 == before_t3_2
    assert all([x in before_t3 for x in [d_area1, d_area2, d_area3, d_area4]])

    after_t2 = crud.disaster_area.get_multi(db, date_time=f"{t2}/")
    after_t2_2 = crud.disaster_area.get_multi(db, date_time=f"{t2}/..")
    assert after_t2 == after_t2_2
    assert len(after_t2) == 3
    assert all([x in after_t2 for x in [d_area3, d_area4, d_area5]])

    at_t2 = crud.disaster_area.get_multi(db, date_time=f"{t2}")
    assert at_t2 == []

    after_t4 = crud.disaster_area.get_multi(db, date_time=f"{t4}/")
    assert after_t4 == []


def test_get_disaster_areas(db: Session) -> None:
    d_area1 = create_new_disaster_area(db, [2, 2])
    d_area2 = create_new_disaster_area(db, [-2, 2])
    d_areas = crud.disaster_area.get_multi(db)
    assert d_area1 in d_areas
    assert d_area2 in d_areas
    for area in [dict({"name": x.name, "a_id": x.id}) for x in d_areas]:
        assert area.get("name")
        assert area.get("a_id")


def test_get_disaster_area_as_feature(db: Session) -> None:
    d_area = create_new_disaster_area(db, [2.4321234124, 2.4321143124])
    d_area2 = crud.disaster_area.get_as_feature(db, d_area.id)
    assert d_area.id == d_area2.id
    assert d_area.name == d_area2.properties.name
    assert d_area2.bbox
    # need to consider storage format of MultiPolygon but feature output as Polygon for single Polygons
    initial_multi_geom = json.loads(db.execute(d_area.geom.st_asgeojson(7)).scalar())
    multi_to_single(initial_multi_geom)
    # TODO: write better tests
    # in d_area the geometry is still stored in EWKB format. After conversion to geojson values are still integer
    # that's why we pass it to the Polygon model again before getting the json value back.
    assert d_area2.geometry == Polygon(**initial_multi_geom)


def test_get_disaster_areas_by_bbox(db: Session) -> None:
    d_area1 = create_new_disaster_area(db, [2, 2])
    d_area2 = create_new_disaster_area(db, [-2, 2])
    d_area3 = create_new_disaster_area(db, [1, 2])
    d_areas = crud.disaster_area.get_multi(db, bbox=(0., 0., 2., 2.))
    assert d_area1 in d_areas
    assert d_area2 not in d_areas
    assert d_area3 in d_areas


def test_update_disaster_area_properties(db: Session) -> None:
    d_area = create_new_disaster_area(db, [2, 2], f=2)
    d_area_update = dict({"properties": {
        "description": "Updated description"
    }})
    d_area2 = crud.disaster_area.update(db, db_obj=d_area, obj_in=d_area_update)
    assert d_area2 == d_area
    assert d_area2.description == d_area_update["properties"]["description"]


def test_update_disaster_area_geometry(db: Session) -> None:
    d_area = create_new_disaster_area(db, [2, 2], f=2)
    geom = create_new_polygon([-1, -1])
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
    # consider multipolygon in storage but polygon during creation
    assert d_area2.geom == db.execute(func.ST_multi(func.ST_GeomFromGeoJSON(geom.json()))).scalar()


def test_remove_disaster_area(db: Session) -> None:
    d_area = create_new_disaster_area(db, [-1, -4], f=2)
    d_area_2 = crud.disaster_area.remove(db, id=d_area.id)
    no_d_area = crud.provider.get(db, id=d_area_2.id)
    assert d_area == d_area_2
    assert not no_d_area
