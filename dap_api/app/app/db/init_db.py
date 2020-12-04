"""
Nothing to do here yet
If we have to initialize the database with users or datasets we can do this here
"""
# TODO:
# add Users: Oscar User
# add Providers: Oscar Provider(from oscar user)
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.db import import_models  # noqa: F401


# make sure all SQL Alchemy models are imported (app.db.import_models) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
# from app.db.base import BaseTable


def create_ds_type_if_missing(db: Session, sub_type: schemas.DisasterSubTypeBaseInDBBase) -> None:
    if not crud.disaster_sub_type.get_by_name(db=db, name=sub_type.name):
        ds_type_obj = schemas.DisasterSubTypeCreate(**sub_type.dict())
        crud.disaster_sub_type.create(db=db, obj_in=ds_type_obj)


def create_d_type_if_missing(db: Session, d_type: schemas.DisasterTypeBaseInDBBase) -> None:
    if not crud.disaster_type.get_by_name(db=db, name=d_type.name):
        d_type_obj = schemas.DisasterTypeCreate(**d_type.dict())
        crud.disaster_type.create(db=db, obj_in=d_type_obj)

    for sub_type in d_type.sub_types:
        create_ds_type_if_missing(db, sub_type)


def create_provider(db: Session, provider: schemas.ProviderInDB) -> None:
    if not crud.provider.get_by_name(db=db, name=provider.name):
        p_obj = schemas.ProviderCreate(**provider.dict())
        crud.provider.create(db=db, obj_in=p_obj)


def create_user(db: Session, user: schemas.User) -> None:
    if not crud.user.get_by_email(db=db, email=user.email):
        u_ubj = schemas.UserCreateFromDb(**user.dict())
        crud.user.create_from_db_entry(db, obj_in=u_ubj)

    for provider in user.providers:
        create_provider(db, provider)


def create_users_and_providers(db: Session) -> None:
    path = Path(__file__).parent.absolute()
    with open(f'{path}/init_data/users.json', 'r') as d_type_file:
        users = json.load(d_type_file)

    users = [schemas.UserInDB(**obj) for obj in users]
    for user in users:
        create_user(db, user)


def create_admin(db: Session) -> None:
    admin = crud.user.get_by_email(db, email=settings.ADMIN_USER)
    if not admin:
        user_in = schemas.UserCreateOut(
            email=settings.ADMIN_USER,
            secret=settings.ADMIN_USER_SECRET,
            is_admin=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841


def create_disaster_types_and_sub_types(db: Session) -> None:
    path = Path(__file__).parent.absolute()  # folder path of this file
    # see https://emergency.copernicus.eu/mapping/ems/domains#_ftnref1
    with open(f'{path}/init_data/d_types.json', 'r') as d_type_file:
        d_types = json.load(d_type_file)

    # convert objects to database entry schema
    d_types = [schemas.DisasterTypeBaseInDBBase(**obj) for obj in d_types]
    for d_type in d_types:
        create_d_type_if_missing(db, d_type)


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # importBaseTable.metadata.create_all(bind=engine)

    create_admin(db)
    create_users_and_providers(db)
    create_disaster_types_and_sub_types(db)


if __name__ == '__main__':
    import logging
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Creating initial data")
    db_session = SessionLocal()
    init_db(db_session)
    logger.info("Initial data created")
