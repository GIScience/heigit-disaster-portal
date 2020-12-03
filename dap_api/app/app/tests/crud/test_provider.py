from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.models import User
from app.schemas import UserCreateOut
from app.schemas.provider import ProviderCreate, ProviderUpdate
from app.security import generate_secret
from app.tests.api.api_v1.test_providers import create_new_provider
from app.tests.utils.utils import random_email, random_lower_string


def test_create_provider(db: Session, provider_owner: User) -> None:
    email = random_email()
    name = random_lower_string(8)
    info = random_lower_string()
    provider_in = ProviderCreate(email=email, name=name, description=info, owner_id=provider_owner.id)
    provider = crud.provider.create(db, obj_in=provider_in)
    assert provider.email == email
    assert provider.name == name
    assert provider.description == info
    assert provider.id


def test_get_provider(db: Session, provider_owner: User) -> None:
    provider = create_new_provider(db, provider_owner)
    provider_2 = crud.provider.get(db, id=provider.id)
    assert provider_2
    assert provider.email == provider_2.email
    assert jsonable_encoder(provider) == jsonable_encoder(provider_2)


def test_get_provider_by_name(db: Session, provider_owner: User) -> None:
    provider = create_new_provider(db, provider_owner)
    provider_2 = crud.provider.get_by_name(db, name=provider.name)
    assert provider_2
    assert provider.description == provider_2.description
    assert jsonable_encoder(provider) == jsonable_encoder(provider_2)


def test_get_provider_by_email(db: Session, provider_owner: User) -> None:
    provider = create_new_provider(db, provider_owner)
    provider_2 = crud.provider.get_by_email(db, email=provider.email)
    assert provider_2
    assert provider.name == provider_2.name
    assert jsonable_encoder(provider) == jsonable_encoder(provider_2)


def test_get_multi_provider_by_owner(db: Session) -> None:
    user_obj = UserCreateOut(email=random_email(), secret=generate_secret())
    user = crud.user.create(db, obj_in=user_obj)
    create_new_provider(db, user)
    create_new_provider(db, user)
    provider_list = crud.provider.get_multi_by_owner(db, owner_id=user.id)
    assert len(provider_list) == 2
    for p in provider_list:
        assert p.owner_id == user.id


def test_update_provider(db: Session, provider_owner: User) -> None:
    provider = create_new_provider(db, provider_owner)
    new_info = "New description"
    provider_in_update = ProviderUpdate(description=new_info)
    provider_2 = crud.provider.update(db, db_obj=provider, obj_in=provider_in_update)
    assert provider_2.email == provider.email
    assert provider_2.name == provider.name
    assert provider_2.id == provider.id
    assert provider_2.owner_id == provider.owner_id
    assert provider_2.description == new_info


def test_remove_provider(db: Session, provider_owner: User) -> None:
    provider = create_new_provider(db, provider_owner)
    provider_2 = crud.provider.remove(db, id=provider.id)
    no_provider = crud.provider.get(db, id=provider_2.id)
    assert jsonable_encoder(provider_2) == jsonable_encoder(provider)
    assert not no_provider
