"""
Initialization of the database with basic data

make sure all SQL Alchemy models are imported (app.db.import_models) before initializing DB
otherwise, SQL Alchemy might fail to initialize relationships properly
for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
"""
import json
from pathlib import Path

from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.db import import_models  # noqa: F401

from app.security import generate_hash
from app.tests.utils.disaster_areas import create_new_disaster_area
from app.logger import log


@log('debug')
def create_ds_type_if_missing(db: Session, sub_type: schemas.DisasterSubTypeBaseInDBBase) -> None:
    if not crud.disaster_sub_type.get_by_name(db=db, name=sub_type.name):
        ds_type_obj = schemas.DisasterSubTypeCreate(**sub_type.dict())
        crud.disaster_sub_type.create(db=db, obj_in=ds_type_obj)


@log('debug')
def create_d_type_if_missing(db: Session, d_type: schemas.DisasterTypeBaseInDBBase) -> None:
    if not crud.disaster_type.get_by_name(db=db, name=d_type.name):
        d_type_obj = schemas.DisasterTypeCreate(**d_type.dict())
        crud.disaster_type.create(db=db, obj_in=d_type_obj)

    for sub_type in d_type.sub_types:
        create_ds_type_if_missing(db, sub_type)


@log('info')
def create_example_provider(db: Session) -> None:
    example_user = crud.user.get_by_email(db, email="user@example.com")
    p_obj = schemas.ProviderCreate(
        owner_id=example_user.id,
        email=EmailStr("provider@example.com"),
        name="Example provider"
    )
    crud.provider.create(db=db, obj_in=p_obj)


@log('info')
def create_example_user(db: Session) -> None:
    u_obj = schemas.UserCreateFromDb(
        email=EmailStr("user@example.com"),
        hashed_secret=generate_hash("example")
    )
    crud.user.create_from_db_entry(db, obj_in=u_obj)


@log('info')
def create_example_disaster_area(db):
    example_provider = crud.provider.get_by_name(db, name="Example provider")
    create_new_disaster_area(
        db,
        p_id=example_provider.id,
        name="Example disaster area",
        info="Example info"
    )


@log('info')
def create_example_custom_speeds(db):
    example_provider = crud.provider.get_by_name(db, name="Example provider")
    speed_obj = schemas.CustomSpeedsCreate(
        properties=schemas.CustomSpeedsProperties(
            name="Example speeds",
            provider_id=example_provider.id
        ),
        content=schemas.CustomSpeedsContent(
            roadSpeeds=schemas.RoadSpeeds(
                primary=80,
                secondary=60,
            )
        )
    )
    crud.custom_speeds.create(db, obj_in=speed_obj)


@log('info')
def create_example_data(db: Session) -> None:
    if crud.user.count(db) == 1:
        create_example_user(db)

    if not crud.provider.count(db):
        create_example_provider(db)

    if not crud.disaster_area.count(db):
        create_example_disaster_area(db)

    if not crud.custom_speeds.count(db):
        create_example_custom_speeds(db)


@log('info')
def create_admin(db: Session) -> None:
    admin = crud.user.get_by_email(db, email=settings.ADMIN_USER)
    if not admin:
        user_in = schemas.UserCreateIn(
            email=settings.ADMIN_USER,
            secret=settings.ADMIN_USER_SECRET,
            is_admin=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841


@log('info')
def create_disaster_types_and_sub_types(db: Session) -> None:
    path = Path(__file__).parent.absolute()  # folder path of this file
    # see https://emergency.copernicus.eu/mapping/ems/domains#_ftnref1
    with open(f'{path}/init_data/d_types.json', 'r') as d_type_file:
        d_types = json.load(d_type_file)

    # convert objects to database entry schema
    d_types = [schemas.DisasterTypeBaseInDBBase(**obj) for obj in d_types]
    for d_type in d_types:
        create_d_type_if_missing(db, d_type)


@log('info')
def init_db(db: Session) -> None:
    create_admin(db)
    create_disaster_types_and_sub_types(db)
    if settings.CREATE_EXAMPLE_DATA_ON_STARTUP:
        create_example_data(db)


if __name__ == '__main__':
    from app.db.session import SessionLocal

    db_session = SessionLocal()
    init_db(db_session)
