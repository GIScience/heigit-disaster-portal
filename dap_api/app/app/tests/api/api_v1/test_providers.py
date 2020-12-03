from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.models import User
from app.tests.utils.provider import create_new_provider
from app.tests.utils.utils import random_email, random_lower_string


def test_create_provider_new_email_new_name(
        client: TestClient, db: Session, provider_owner: User
) -> None:
    p_mail = random_email()
    p_name = random_lower_string(8)

    data = {"owner_id": provider_owner.id, "email": p_mail, "name": p_name}
    r = client.post(
        f"{settings.API_V1_STR}/collections/providers/", json=data,
    )
    assert 200 <= r.status_code < 300
    created_provider = r.json()
    provider_by_mail = crud.provider.get_by_email(db, email=p_mail)
    provider_by_name = crud.provider.get_by_name(db, name=p_name)
    assert provider_by_mail
    assert provider_by_name
    assert provider_by_mail.email == created_provider["email"]
    assert provider_by_mail.name == created_provider["name"]
    assert provider_by_name.email == created_provider["email"]
    assert provider_by_name.name == created_provider["name"]


def test_create_provider_invalid_owner(
        client: TestClient
) -> None:
    data = {"owner_id": -1, "email": random_email(), "name": random_lower_string(8)}
    r = client.post(
        f"{settings.API_V1_STR}/collections/providers/", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert "_id" not in r_obj


def test_create_provider_existing_name(
        client: TestClient, db: Session, provider_owner: User
) -> None:
    p = create_new_provider(db, provider_owner)
    data = {"owner_id": provider_owner.id, "email": random_email(), "name": p.name}
    r = client.post(
        f"{settings.API_V1_STR}/collections/providers/", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert "_id" not in r_obj


def test_create_provider_existing_email(
        client: TestClient, db: Session, provider_owner: User
) -> None:
    p = create_new_provider(db, provider_owner)
    data = {"owner_id": provider_owner.id, "email": p.email, "name": random_lower_string(8)}
    r = client.post(
        f"{settings.API_V1_STR}/collections/providers/", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert "_id" not in r_obj


def test_create_provider_missing_email(
        client: TestClient, provider_owner: User
) -> None:
    data = {"owner_id": provider_owner.id, "name": random_lower_string(8)}
    r = client.post(
        f"{settings.API_V1_STR}/collections/providers/", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"][1] == "email"
    assert r_obj["detail"][0]["msg"] == "field required"


def test_create_provider_missing_name(
        client: TestClient, provider_owner: User
) -> None:
    data = {"owner_id": provider_owner.id, "email": random_email()}
    r = client.post(
        f"{settings.API_V1_STR}/collections/providers/", json=data,
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"][1] == "name"
    assert r_obj["detail"][0]["msg"] == "field required"


def test_get_existing_provider(
        client: TestClient, db: Session, provider_owner: User
) -> None:
    p = create_new_provider(db, provider_owner)
    provider_id = p.id
    r = client.get(
        f"{settings.API_V1_STR}/collections/providers/items/{provider_id}",
    )
    assert 200 <= r.status_code < 300
    api_provider = r.json()
    existing_provider = crud.provider.get_by_email(db, email=p.email)
    assert existing_provider
    assert existing_provider.email == api_provider["email"]


def test_get_not_existing_provider(
        client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/collections/providers/items/{-1}",
    )
    assert r.status_code == 404
    assert r.json()["detail"]


def test_get_provider_negative_id(
        client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/collections/providers/items/{-1}",
    )
    assert r.status_code == 404
    assert r.json()["detail"]


def test_update_existing_provider(
        client: TestClient, db: Session, provider_owner: User
) -> None:
    p = create_new_provider(db, provider_owner)
    r = crud.provider.get(db, p.id)
    assert r.description == "Disaster area provider"
    provider_id = p.id
    r = client.put(f"{settings.API_V1_STR}/collections/providers/items/{provider_id}", json={"description": "New Info"})

    assert r.status_code == 200
    assert r.json()["description"] == "New Info"


def test_update_not_existing_provider(
        client: TestClient
) -> None:
    r = client.put(f"{settings.API_V1_STR}/collections/providers/items/{-1}", json={"description": "New Info"})
    assert r.status_code == 404
    assert r.json()["detail"]


def test_delete_existing_provider(
        client: TestClient, db: Session, provider_owner: User
) -> None:
    p = create_new_provider(db, provider_owner)
    provider_id = p.id

    r = client.delete(f"{settings.API_V1_STR}/collections/providers/items/{provider_id}")
    assert r.status_code == 200
    assert crud.provider.get(db, id=provider_id) is None


def test_delete_not_existing_provider(
        client: TestClient
) -> None:
    r = client.delete(f"{settings.API_V1_STR}/collections/providers/items/{-1}")
    assert r.status_code == 404
    assert r.json()["detail"]


def test_retrieve_providers(
        client: TestClient, db: Session, provider_owner: User
) -> None:
    create_new_provider(db, provider_owner)
    create_new_provider(db, provider_owner)

    r = client.get(f"{settings.API_V1_STR}/collections/providers/")
    all_providers = r.json()

    assert len(all_providers) > 1
    for item in all_providers:
        assert "email" in item
        assert "name" in item
        assert "owner_id" in item
