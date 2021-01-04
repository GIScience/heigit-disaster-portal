from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.schemas.disaster_area import DisasterAreaPropertiesCreate
from app.tests.utils.disaster_areas import create_new_disaster_area
from app.tests.utils.disaster_areas import create_new_polygon, create_new_properties
from app.tests.utils.utils import random_lower_string


def test_create_disaster_area(
        client: TestClient
) -> None:
    d_area_props = create_new_properties()
    d_area_geom = create_new_polygon()

    r = client.post(
        f"{settings.API_V1_STR}/collections/disaster_areas/items", json={
            "type": "Feature",
            "geometry": d_area_geom.dict(),
            "properties": d_area_props.dict()
        },
    )
    assert 200 <= r.status_code < 300
    created_d_area = r.json()
    assert created_d_area
    assert created_d_area.get("properties").get("created")
    assert created_d_area.get("properties").get("area")
    assert created_d_area.get("properties").get("d_type_id") == d_area_props.d_type_id
    assert created_d_area.get("properties").get("ds_type_id") == d_area_props.ds_type_id
    assert created_d_area.get("properties").get("description") == d_area_props.description
    assert created_d_area.get("properties").get("name") == d_area_props.name


# runs the following test once for each tuple (coords, e_loc, e_msg) in the array
@pytest.mark.parametrize(
    "coords,e_loc,e_msg",
    [
        ([[[0, 0], [0, 1], [0, 0]]],
         ["body", "geometry", "coordinates"],
         "All linear rings must have four or more coordinates"),
        ([[[0, 0], [0, 1], [1, 0], [1, 2]]],
         ["body", "geometry", "coordinates"],
         "All linear rings have the same start and end coordinates"),
        ([[[0, 0], [0, 1], [1, 0], [1, 1], [0, 0]]],
         ["body", "geometry"],
         "Geometry not valid: Self-intersection[0.5 0.5]"),
    ]
)
def test_create_d_area_invalid_geom(
        client: TestClient,
        coords: List[List[List[float]]],
        e_loc: List[str],
        e_msg: str
) -> None:
    new_props = create_new_properties()
    data = {
        "type": "Feature",
        "properties": new_props.dict(),
        "geometry": {
            "type": "Polygon",
            "coordinates": coords
        }
    }
    r = client.post(
        f"{settings.API_V1_STR}/collections/disaster_areas/items", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == e_loc
    assert r_obj["detail"][0]["msg"] == e_msg


def test_create_d_area_existing_name(
        client: TestClient, db: Session
) -> None:
    d_area = create_new_disaster_area(db)
    d_area_geom = create_new_polygon()
    new_props = DisasterAreaPropertiesCreate(
        name=d_area.name,
        d_type_id=3,
        provider_id=7,
        description=random_lower_string(20)
    )
    data = {
        "type": "Feature",
        "properties": new_props.dict(),
        "geometry": d_area_geom.dict()
    }
    r = client.post(
        f"{settings.API_V1_STR}/collections/disaster_areas/items", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert "_id" not in r_obj


def test_create_d_area_missing_name(
        client: TestClient
) -> None:
    d_area_geom = create_new_polygon()
    new_props = DisasterAreaPropertiesCreate(
        name="deleted",
        d_type_id=3,
        provider_id=7,
        description=random_lower_string(20)
    )
    del new_props.name
    data = {
        "type": "Feature",
        "properties": new_props.dict(),
        "geometry": d_area_geom.dict()
    }
    r = client.post(
        f"{settings.API_V1_STR}/collections/disaster_areas/items", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["body", "properties", "name"]
    assert r_obj["detail"][0]["msg"] == "field required"


def test_get_existing_d_area(
        client: TestClient, db: Session
) -> None:
    d_area = create_new_disaster_area(db)
    r = client.get(
        f"{settings.API_V1_STR}/collections/disaster_areas/items/{d_area.id}",
    )
    assert 200 <= r.status_code < 300
    api_d_area = r.json()
    assert api_d_area
    assert api_d_area.get("id") == d_area.id
    assert api_d_area.get("properties").get("name") == d_area.name
    assert api_d_area.get("properties").get("description") == d_area.description
    assert api_d_area.get("properties").get("d_type_id") == d_area.d_type_id
    assert api_d_area.get("properties").get("ds_type_id") == d_area.ds_type_id
    assert api_d_area.get("properties").get("provider_id") == d_area.provider_id


def test_get_d_area_negative_id(
        client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/collections/disaster_areas/items/{-1}",
    )
    assert r.status_code == 404
    assert r.json()["detail"]


def test_update_existing_d_area_properties(
        client: TestClient, db: Session
) -> None:
    d_area = create_new_disaster_area(db)
    previous_description = d_area.description
    r = client.put(f"{settings.API_V1_STR}/collections/disaster_areas/items/{d_area.id}",
                   json={
                       "properties": {
                           "description": "New Info"
                       }
                   })
    updated_area = r.json()
    assert r.status_code == 200
    assert updated_area.get("properties").get("description") == "New Info"
    assert updated_area.get("properties").get("description") != previous_description
    assert d_area == crud.disaster_area.get(db, updated_area.get("id"))


def test_update_existing_d_area_geometry(
        client: TestClient, db: Session
) -> None:
    d_area = create_new_disaster_area(db)
    d_area_feature = crud.disaster_area.get_as_feature(db, d_area.id)
    geom = create_new_polygon()
    data = {"geometry": geom.dict()}
    r = client.put(f"{settings.API_V1_STR}/collections/disaster_areas/items/{d_area.id}",
                   json=data)

    assert r.status_code == 200
    assert r.json()["geometry"] != d_area_feature.geometry.json()


def test_update_not_existing_d_area(
        client: TestClient
) -> None:
    r = client.put(f"{settings.API_V1_STR}/collections/disaster_areas/items/{-1}",
                   json={
                       "properties": {
                           "description": "New Info"
                       }
                   })
    assert r.status_code == 404
    assert r.json()["detail"]


def test_delete_existing_d_area(
        client: TestClient, db: Session
) -> None:
    d_area = create_new_disaster_area(db)
    r = client.delete(f"{settings.API_V1_STR}/collections/disaster_areas/items/{d_area.id}")
    assert r.status_code == 200
    r_obj = r.json()
    assert crud.disaster_area.get(db, id=r_obj.get("id"))


def test_delete_not_existing_d_area(
        client: TestClient
) -> None:
    r = client.delete(f"{settings.API_V1_STR}/collections/disaster_areas/items/{-1}")
    assert r.status_code == 404
    assert r.json()["detail"]


def test_retrieve_d_areas(
        client: TestClient, db: Session
) -> None:
    create_new_disaster_area(db)
    create_new_disaster_area(db)

    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items")
    all_d_areas = r.json()

    assert len(all_d_areas) > 1
    for area in all_d_areas.get("features"):
        assert "name" in area["properties"]
        assert "provider_id" in area["properties"]
        assert "d_type_id" in area["properties"]
        assert "id" in area
