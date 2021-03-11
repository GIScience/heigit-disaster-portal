import json
from typing import Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import crud
from app.config import settings
from app.tests.utils.custom_speeds import create_new_custom_speeds


def test_create_custom_speeds(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    name = "Test"
    desc = "Test set of custom speeds"
    r = client.post(
        f"{settings.API_V1_STR}/collections/custom_speeds/items",
        json={
            "content": {
                "unit": "kmh",
                "roadSpeeds": {
                    "motorway": 0,
                    "trunk": 0
                },
                "surfaceSpeeds": {
                    "paved": 0,
                    "concrete:lanes": 50,
                    "gravel": 75
                }
            },
            "properties": {
                "name": name,
                "description": desc,
                "provider_id": 1,
            }
        },
        headers=admin_auth_header
    )
    assert 200 <= r.status_code < 300
    created_custom_speeds = r.json()
    assert created_custom_speeds
    assert created_custom_speeds.get("id")
    assert created_custom_speeds.get("properties").get("created")
    assert created_custom_speeds.get("properties").get("name") == name
    assert created_custom_speeds.get("properties").get("description") == desc
    assert created_custom_speeds.get("content").get("surfaceSpeeds").get("gravel") == 75


def test_create_custom_speeds_invalid_content(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    name = "Test"
    desc = "Test set of custom speeds"
    r = client.post(
        f"{settings.API_V1_STR}/collections/custom_speeds/items",
        json={
            "content": {
                "unit": "kmh",
                "roadSpeeds": {
                    "invalid_road_type_key": 0,
                    "trunk": 0
                },
                "surfaceSpeeds": {
                    "paved": 0,
                    "concrete:lanes": 50,
                    "gravel": 75
                }
            },
            "properties": {
                "name": name,
                "description": desc,
                "provider_id": 1,
            }
        },
        headers=admin_auth_header
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ['body', 'content', 'roadSpeeds', 'invalid_road_type_key']
    assert r_obj["detail"][0]["msg"] == "extra fields not permitted"


def test_create_custom_speeds_invalid_content_unit(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    name = "Test"
    desc = "Test set of custom speeds"
    r = client.post(
        f"{settings.API_V1_STR}/collections/custom_speeds/items",
        json={
            "content": {
                "unit": "unknown unit",
                "roadSpeeds": {
                    "motorway": 0,
                    "trunk": 0
                },
                "surfaceSpeeds": {
                    "paved": 0,
                    "concrete:lanes": 50,
                    "gravel": 75
                }
            },
            "properties": {
                "name": name,
                "description": desc,
                "provider_id": 1,
            }
        },
        headers=admin_auth_header
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ['body', 'content', 'unit']
    assert r_obj["detail"][0]["msg"] == "value is not a valid enumeration member; permitted: 'kmh', 'mph'"


def test_create_custom_speeds_missing_name(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/collections/custom_speeds/items",
        json={
            "content": {
                "unit": "kmh",
                "roadSpeeds": {
                    "motorway": 0,
                    "trunk": 0
                },
                "surfaceSpeeds": {
                    "paved": 0,
                    "concrete:lanes": 50,
                    "gravel": 75
                }
            },
            "properties": {
                "description": "description",
                "provider_id": 1,
            }
        },
        headers=admin_auth_header
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["body", "properties", "name"]
    assert r_obj["detail"][0]["msg"] == "field required"


def test_get_existing_custom_speeds(
        client: TestClient, db: Session
) -> None:
    custom_speeds = create_new_custom_speeds(db)
    r = client.get(
        f"{settings.API_V1_STR}/collections/custom_speeds/items/{custom_speeds.id}",
    )
    assert 200 <= r.status_code < 300
    api_custom_speeds = r.json()
    assert api_custom_speeds
    assert api_custom_speeds.get("id") == custom_speeds.id
    assert api_custom_speeds.get("properties").get("name") == custom_speeds.name
    assert api_custom_speeds.get("properties").get("description") == custom_speeds.description
    assert api_custom_speeds.get("properties").get("provider_id") == custom_speeds.provider_id


def test_get_custom_speeds_negative_id(
        client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/collections/custom_speeds/items/{-1}",
    )
    assert r.status_code == 404
    assert r.json()["detail"]


def test_update_existing_custom_speeds_properties(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    custom_speeds = create_new_custom_speeds(db)
    r = client.put(
        f"{settings.API_V1_STR}/collections/custom_speeds/items/{custom_speeds.id}",
        json={
           "properties": {
               "description": "New Info"
           }
        },
        headers=admin_auth_header
    )
    updated = r.json()
    assert r.status_code == 200
    assert updated.get("properties").get("description") == "New Info"


def test_update_existing_custom_speeds_content(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    custom_speeds = create_new_custom_speeds(db)
    r = client.put(
        f"{settings.API_V1_STR}/collections/custom_speeds/items/{custom_speeds.id}",
        json=json.loads('''{
            "content": {
                "unit": "kmh",
                "roadSpeeds": {
                    "motorway": 100,
                    "trunk": 100
                },
                "surfaceSpeeds": {
                    "paved": 10,
                    "concrete:lanes": 50,
                    "gravel": 75
                }
            }
        }'''),
        headers=admin_auth_header
    )
    assert r.status_code == 200
    assert json.dumps(r.json()["content"]) != custom_speeds.content


def test_update_not_existing_custom_speeds(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    r = client.put(
        f"{settings.API_V1_STR}/collections/custom_speeds/items/{-1}",
        json={
            "properties": {
                "description": "New Info"
            }
        },
        headers=admin_auth_header
    )
    assert r.status_code == 404
    assert r.json()["detail"]


def test_delete_existing_custom_speeds(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    cs = create_new_custom_speeds(db)
    r = client.delete(f"{settings.API_V1_STR}/collections/custom_speeds/items/{cs.id}", headers=admin_auth_header)
    assert r.status_code == 200
    r_obj = r.json()
    assert crud.custom_speeds.get(db, cs_id=r_obj.get("id"))


def test_delete_not_existing_custom_speeds(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    r = client.delete(f"{settings.API_V1_STR}/collections/custom_speeds/items/{-1}", headers=admin_auth_header)
    assert r.status_code == 404
    assert r.json()["detail"]


def test_retrieve_custom_speeds(
        client: TestClient, db: Session
) -> None:
    create_new_custom_speeds(db)
    create_new_custom_speeds(db)

    r = client.get(f"{settings.API_V1_STR}/collections/custom_speeds/items")
    all_cs = r.json()

    assert len(all_cs) > 1
    for cs in all_cs:
        assert "name" in cs["properties"]
        assert "provider_id" in cs["properties"]
        assert "id" in cs
