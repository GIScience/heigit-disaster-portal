from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.schemas.user import UserCreateOut
from app.security import generate_hash, generate_secret
from app.tests.utils.utils import random_email


def test_create_user_new_email(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    username = random_email()
    data = {"email": username}
    r = client.post(
        f"{settings.API_V1_STR}/collections/users/items",
        json=data,
        headers=admin_auth_header
    )
    assert 200 <= r.status_code < 300
    created_user = r.json()
    user = crud.user.get_by_email(db, email=username)
    assert user
    assert user.email == created_user["email"]
    assert user.hashed_secret == generate_hash(created_user["secret"])


def test_create_user_existing_email(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    user_obj = UserCreateOut(email=random_email(), secret=generate_secret())
    crud.user.create(db, obj_in=user_obj)
    data = {"email": user_obj.email}
    r = client.post(
        f"{settings.API_V1_STR}/collections/users/items",
        json=data,
        headers=admin_auth_header
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert "_id" not in r_obj
    assert r_obj["detail"]


def test_create_user_invalid_email(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    data = {"email": "invalid_email"}
    r = client.post(
        f"{settings.API_V1_STR}/collections/users/items",
        json=data,
        headers=admin_auth_header
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"][1] == "email"
    assert r_obj["detail"][0]["msg"] == "value is not a valid email address"


def test_get_existing_user(
        client: TestClient, db: Session
) -> None:
    username = random_email()
    user_obj = UserCreateOut(email=username, secret=generate_secret())
    user = crud.user.create(db, obj_in=user_obj)
    user_id = user.id
    r = client.get(
        f"{settings.API_V1_STR}/collections/users/items/{user_id}",
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = crud.user.get_by_email(db, email=username)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_get_not_existing_user(
        client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/collections/users/items/{-1}",
    )
    assert r.status_code == 404
    r_obj = r.json()
    assert r_obj["detail"]


def test_update_existing_user_email(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    user_obj = UserCreateOut(email=random_email(), secret=generate_secret())
    user = crud.user.create(db, obj_in=user_obj)
    r = client.put(f"{settings.API_V1_STR}/collections/users/items/{user.id}",
                   json={"email": "new@mail.com"},
                   headers=admin_auth_header)
    assert r.status_code == 200
    assert r.json()["email"] == "new@mail.com"


def test_update_existing_user_secret(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:

    user_obj = UserCreateOut(email=random_email(), secret=generate_secret())
    user = crud.user.create(db, obj_in=user_obj)
    assert user.hashed_secret == generate_hash(user_obj.secret)
    r = client.put(f"{settings.API_V1_STR}/collections/users/items/{user.id}",
                   json={"secret": "new_secret"},
                   headers=admin_auth_header)
    r_obj = r.json()
    db.refresh(user)
    db_user = crud.user.get(db, id=user.id)

    assert r.status_code == 200
    assert not r_obj.get("secret")
    assert db_user.hashed_secret == generate_hash("new_secret")


def test_update_not_existing_user_email(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    r = client.put(f"{settings.API_V1_STR}/collections/users/items/{-1}",
                   json={"email": "new@mail.com"},
                   headers=admin_auth_header)
    assert r.status_code == 404
    assert r.json()["detail"]


def test_delete_existing_user(
        client: TestClient, db: Session,
        admin_auth_header: Dict[str, str]
) -> None:
    username = random_email()
    user_obj = UserCreateOut(email=username, secret=generate_secret())
    user = crud.user.create(db, obj_in=user_obj)
    user_id = user.id

    r = client.delete(f"{settings.API_V1_STR}/collections/users/items/{user_id}",
                      headers=admin_auth_header)
    assert r.status_code == 200
    assert crud.user.get(db, id=user_id) is None


def test_delete_not_existing_user(
        client: TestClient,
        admin_auth_header: Dict[str, str]
) -> None:
    r = client.delete(f"{settings.API_V1_STR}/collections/users/items/{-1}",
                      headers=admin_auth_header)
    assert r.status_code == 404
    assert r.json()["detail"]


def test_retrieve_users(
        client: TestClient, db: Session
) -> None:
    username = random_email()
    user_obj = UserCreateOut(email=username, secret=generate_secret())
    crud.user.create(db, obj_in=user_obj)

    username2 = random_email()
    user_obj2 = UserCreateOut(email=username2, secret=generate_secret())
    crud.user.create(db, obj_in=user_obj2)

    r = client.get(f"{settings.API_V1_STR}/collections/users/items")
    all_users = r.json()

    assert len(all_users) > 1
    for item in all_users:
        assert "email" in item
