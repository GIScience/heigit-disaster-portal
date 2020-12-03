from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.config import settings


def test_retrieve_disaster_types(
        client: TestClient, db: Session
) -> None:
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_types/")
    assert 200 <= r.status_code < 300
    d_type_collection = r.json()
    db_entries = crud.disaster_type.get_multi(db)
    assert len(d_type_collection) == len(db_entries)
    for d_type in d_type_collection:
        assert d_type.get("name")
        assert d_type.get("id")


def test_get_existing_d_type_by_name(
        client: TestClient
) -> None:
    d_type = "flood"
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_types/items/{d_type}")
    r_obj = r.json()
    assert 200 <= r.status_code < 300
    assert "sub_types" in r_obj.keys()
    assert r_obj.get("name") == d_type


def test_get_not_existing_d_type_by_name(
        client: TestClient
) -> None:
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_types/items/{'not_a_disaster_type'}")
    assert r.status_code == 404
    assert r.json()["detail"]


def test_get_existing_d_type_by_id(
        client: TestClient
) -> None:
    d_type_id = 1
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_types/items/{d_type_id}")
    r_obj = r.json()
    assert 200 <= r.status_code < 300
    assert "sub_types" in r_obj.keys()
    assert r_obj.get("id") == d_type_id


def test_get_not_existing_d_type_by_id(
        client: TestClient
) -> None:
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_types/items/{-1}")
    r_obj = r.json()
    assert r.status_code == 404
    assert r_obj["detail"]
