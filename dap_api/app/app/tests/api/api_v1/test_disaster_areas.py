from datetime import datetime, timedelta
from typing import List, Dict

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
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    d_area_props = create_new_properties()
    d_area_geom = create_new_polygon()

    r = client.post(
        f"{settings.API_V1_STR}/collections/disaster_areas/items", json={
            "type": "Feature",
            "geometry": d_area_geom.dict(),
            "properties": d_area_props.dict()
        },
        headers=admin_auth_header
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
         "Linear rings must have four or more coordinates"),
        ([[[]]],
         ["body", "geometry", "coordinates"],
         "Linear rings must have four or more coordinates"),
        ([[[0, 0], [0, 1], [1, 0], [1, 2]]],
         ["body", "geometry", "coordinates"],
         "Linear rings must have the same start and end coordinates"),
        ([[[0, 0], [0, 1], [1, 0], [0, 0.0000000000000000001]]],
         ["body", "geometry", "coordinates"],
         "Linear rings must have the same start and end coordinates"),
        ([[[0, 0], [0, 1, 2], [1, 0], [1, 2], [0, 0]]],
         ["body", "geometry", "coordinates"],
         "Coordinates must have exactly two values"),
        ([[[0, 0], [], [1, 0], [1, 2], [0, 0]]],
         ["body", "geometry", "coordinates"],
         "Coordinates must have exactly two values"),
        ([[[0, 0], [200, 1], [1, 0], [1, 2], [0, 0]]],
         ["body", "geometry", "coordinates"],
         "Longitude needs to be in range +-180"),
        ([[[0, 0], [-200, 1], [1, 0], [1, 2], [0, 0]]],
         ["body", "geometry", "coordinates"],
         "Longitude needs to be in range +-180"),
        ([[[0, 0], [0, 100], [1, 0], [1, 2], [0, 0]]],
         ["body", "geometry", "coordinates"],
         "Latitude needs to be in range +-90"),
        ([[[0, 0], [0, -90.00001], [1, 0], [1, 2], [0, 0]]],
         ["body", "geometry", "coordinates"],
         "Latitude needs to be in range +-90"),
        ([[[0, 0], [0, 1], [1, 0], [1, 1], [0, 0]]],
         ["body", "geometry"],
         "Geometry not valid: Self-intersection[0.5 0.5]"),
    ]
)
def test_create_d_area_invalid_geom(
        client: TestClient,
        admin_auth_header: Dict[str, str],
        coords: List[List[List[float]]],
        e_loc: List[str],
        e_msg: str,
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
        f"{settings.API_V1_STR}/collections/disaster_areas/items", json=data, headers=admin_auth_header
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == e_loc
    assert r_obj["detail"][0]["msg"] == e_msg


def test_create_d_area_existing_name(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    d_area = create_new_disaster_area(db)
    d_area_geom = create_new_polygon()
    new_props = DisasterAreaPropertiesCreate(
        name=d_area.name,
        d_type_id=3,
        provider_id=1,
        description=random_lower_string(20)
    )
    data = {
        "type": "Feature",
        "properties": new_props.dict(),
        "geometry": d_area_geom.dict()
    }
    r = client.post(
        f"{settings.API_V1_STR}/collections/disaster_areas/items",
        json=data,
        headers=admin_auth_header
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert "_id" not in r_obj
    assert r_obj.get("code") == 5409


def test_create_d_area_missing_name(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    d_area_geom = create_new_polygon()
    new_props = DisasterAreaPropertiesCreate(
        name="deleted",
        d_type_id=3,
        provider_id=1,
        description=random_lower_string(20)
    )
    del new_props.name
    data = {
        "type": "Feature",
        "properties": new_props.dict(),
        "geometry": d_area_geom.dict()
    }
    r = client.post(
        f"{settings.API_V1_STR}/collections/disaster_areas/items",
        json=data,
        headers=admin_auth_header
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
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    d_area = create_new_disaster_area(db)
    previous_description = d_area.description
    r = client.put(f"{settings.API_V1_STR}/collections/disaster_areas/items/{d_area.id}",
                   json={
                       "properties": {
                           "description": "New Info"
                       }
                   },
                   headers=admin_auth_header)
    updated_area = r.json()
    assert r.status_code == 200
    assert updated_area.get("properties").get("description") == "New Info"
    assert updated_area.get("properties").get("description") != previous_description
    assert d_area == crud.disaster_area.get(db, updated_area.get("id"))


def test_update_existing_d_area_geometry(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    d_area = create_new_disaster_area(db)
    d_area_feature = crud.disaster_area.get_as_feature(db, d_area.id)
    geom = create_new_polygon()
    data = {"geometry": geom.dict()}
    r = client.put(f"{settings.API_V1_STR}/collections/disaster_areas/items/{d_area.id}",
                   json=data,
                   headers=admin_auth_header)

    assert r.status_code == 200
    assert r.json()["geometry"] != d_area_feature.geometry.json()


def test_update_not_existing_d_area(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    r = client.put(f"{settings.API_V1_STR}/collections/disaster_areas/items/{-1}",
                   json={
                       "properties": {
                           "description": "New Info"
                       }
                   },
                   headers=admin_auth_header)
    assert r.status_code == 404
    assert r.json()["detail"]


def test_delete_existing_d_area(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    d_area = create_new_disaster_area(db)
    r = client.delete(f"{settings.API_V1_STR}/collections/disaster_areas/items/{d_area.id}",
                      headers=admin_auth_header)
    assert r.status_code == 200
    r_obj = r.json()
    assert crud.disaster_area.get(db, id=r_obj.get("id"))


def test_delete_not_existing_d_area(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    r = client.delete(f"{settings.API_V1_STR}/collections/disaster_areas/items/{-1}",
                      headers=admin_auth_header)
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


def test_retrieve_d_areas_of_type(
        client: TestClient, db: Session
) -> None:
    create_new_disaster_area(db, d_id=4)
    create_new_disaster_area(db, d_id=6)
    create_new_disaster_area(db, d_id=6)

    # Has 1 area with d_type_id 4
    r2 = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                    params={"d_type_id": 4})

    json_areas_2 = r2.json()
    assert len(json_areas_2) > 1
    areas_4 = json_areas_2.get("features")
    assert len(areas_4) == 1
    assert areas_4[0]["properties"]["d_type_id"] == 4

    # Has 2 areas with d_type_id 6
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"d_type_id": 6})
    json_areas = r.json()

    assert len(json_areas) > 1
    areas_6 = json_areas.get("features")
    assert len(areas_6) == 2
    for area in areas_6:
        assert area["properties"]["d_type_id"] == 6

    # invalid d_type_id
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"d_type_id": -1})
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["query", "d_type_id"]
    assert r_obj["detail"][0]["msg"] == "ensure this value is greater than 0"


def test_retrieve_d_areas_at_datetime(
        client: TestClient, db: Session
) -> None:
    # area existing at datetime
    a = create_new_disaster_area(db)
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"datetime": str(a.created)})
    datetime_response = r.json()

    assert r.status_code == 200
    f = datetime_response.get("features")
    assert len(f) == 1
    assert f[0]['properties']['name'] == a.name

    # no area at datetime
    t = datetime.now()
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"datetime": t})
    r_obj = r.json()
    assert len(r_obj.get("features")) == 0


@pytest.mark.parametrize(
    "date_time,e_msg",
    [
        (" ",
         "Invalid timestamp  : ISO string too short"),
        ("2018-02-12T23:20:50ss",
         "Invalid timestamp 2018-02-12T23:20:50ss: Unused components in ISO string"),
        ("2018-02-40T23:20:50",
         "Invalid timestamp 2018-02-40T23:20:50: day is out of range for month"),
        ("2018-02-12T24:20:50",
         "Invalid timestamp 2018-02-12T24:20:50: Hour may only be 24 at 24:00:00.000"),
        ("2018-13-12T23:20:50",
         "Invalid timestamp 2018-13-12T23:20:50: month must be in 1..12"),
        ("2018-12-12T23:20:70",
         "Invalid timestamp 2018-12-12T23:20:70: second must be in 0..59")
    ]
)
def test_retrieve_d_areas_malformed_datetime(
        client: TestClient,
        date_time: str,
        e_msg: str
) -> None:
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"datetime": date_time})
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["query", "datetime"]
    assert r_obj["detail"][0]["msg"] == e_msg


def test_retrieve_d_areas_at_datetime_interval(
        client: TestClient, db: Session
) -> None:
    t1 = datetime.now()
    a1 = create_new_disaster_area(db)
    t2 = a1.created + timedelta(microseconds=5)
    a2 = create_new_disaster_area(db)

    # closed interval
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"datetime": f"{t1}/{t2}"})
    r_obj = r.json()
    assert r.status_code == 200
    f = r_obj.get("features")
    assert len(f) == 1
    assert f[0]['properties']['name'] == a1.name

    # open end
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"datetime": f"{t2}/"})
    r_obj = r.json()
    assert r.status_code == 200
    f = r_obj.get("features")
    assert len(f) == 1
    assert f[0]['properties']['name'] == a2.name

    # open start
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_areas/items",
                   params={"datetime": f"../{t2}"})
    r_obj = r.json()
    assert r.status_code == 200
    f_ids = [f.get("id") for f in r_obj.get("features")]
    assert a2.id not in f_ids
    assert a1.id in f_ids
