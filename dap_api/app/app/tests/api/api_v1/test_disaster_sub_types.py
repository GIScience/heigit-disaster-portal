from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.config import settings


def test_retrieve_disaster_sub_types(
        client: TestClient, db: Session
) -> None:
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_sub_types/")
    assert 200 <= r.status_code < 300
    ds_type_collection = r.json()
    db_entries = crud.disaster_sub_type.get_multi(db)
    assert len(ds_type_collection) == len(db_entries)
    for ds_type in ds_type_collection:
        assert ds_type.get("name")
        assert ds_type.get("id")


def test_get_existing_ds_type_by_name(
        client: TestClient
) -> None:
    ds_type = "cold_wave"
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_sub_types/items/{ds_type}")
    r_obj = r.json()
    assert 200 <= r.status_code < 300
    assert "parent_id" in r_obj.keys()
    assert r_obj.get("name") == ds_type


def test_get_not_existing_ds_type_by_name(
        client: TestClient
) -> None:
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_sub_types/items/{'not_a_disaster_sub_type'}")
    assert r.status_code == 404
    assert r.json()["detail"]


def test_get_existing_ds_type_by_id(
        client: TestClient
) -> None:
    ds_type_id = 1
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_sub_types/items/{ds_type_id}")
    r_obj = r.json()
    assert 200 <= r.status_code < 300
    assert "parent_id" in r_obj.keys()
    assert r_obj.get("id") == ds_type_id


def test_get_not_existing_ds_type_by_id(
        client: TestClient
) -> None:
    r = client.get(f"{settings.API_V1_STR}/collections/disaster_sub_types/items/{-1}")
    r_obj = r.json()
    assert r.status_code == 404
    assert r_obj["detail"]
