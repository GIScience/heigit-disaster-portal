from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.schemas.user import UserCreateOut, UserUpdate
from app.tests.utils.utils import random_email, random_lower_string


def test_create_user(db: Session) -> None:
    email = random_email()
    secret = random_lower_string()
    user_in = UserCreateOut(email=email, secret=secret)
    user = crud.user.create(db, obj_in=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_secret")


def test_check_if_user_is_active(db: Session) -> None:
    email = random_email()
    secret = random_lower_string()
    user_in = UserCreateOut(email=email, secret=secret)
    user = crud.user.create(db, obj_in=user_in)
    is_active = crud.user.is_active(user)
    assert is_active is True


def test_check_if_user_is_admin(db: Session) -> None:
    email = random_email()
    secret = random_lower_string()
    user_in = UserCreateOut(email=email, secret=secret, is_admin=True)
    user = crud.user.create(db, obj_in=user_in)

    is_admin = crud.user.is_admin(user)
    assert is_admin is True


def test_check_if_user_is_admin_normal_user(db: Session) -> None:
    user_in = UserCreateOut(email=random_email(), secret=random_lower_string())
    user = crud.user.create(db, obj_in=user_in)
    is_admin = crud.user.is_admin(user)
    assert is_admin is False


def test_get_user(db: Session) -> None:
    email = random_email()
    secret = random_lower_string()
    user_in = UserCreateOut(email=email, secret=secret, is_admin=True)
    user = crud.user.create(db, obj_in=user_in)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    email = random_email()
    secret = random_lower_string()
    user_in = UserCreateOut(email=email, secret=secret, is_admin=True)
    user = crud.user.create(db, obj_in=user_in)
    new_secret = random_lower_string()
    user_in_update = UserUpdate(secret=new_secret, is_admin=True)
    crud.user.update(db, db_obj=user, obj_in=user_in_update)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
