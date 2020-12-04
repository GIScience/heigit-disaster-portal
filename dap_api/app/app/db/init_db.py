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


def add_ds_type_if_missing(db: Session, ds_type: dict, parent_id: int):
    s_name, s_info = list(ds_type.items())[0]
    if not crud.disaster_sub_type.get_by_name(db=db, name=s_name):
        ds_type_obj = schemas.DisasterSubTypeCreate(
            name=s_name,
            description=s_info,
            parent_id=parent_id
        )
        crud.disaster_sub_type.create(db=db, obj_in=ds_type_obj)


def add_d_type_if_missing(db: Session, d_type):
    name, info = list(d_type.items())[0]
    db_entry = crud.disaster_type.get_by_name(db=db, name=name)
    if not db_entry:
        d_type_obj = schemas.DisasterTypeCreate(
            name=name,
            description=info
        )
        db_entry = crud.disaster_type.create(db=db, obj_in=d_type_obj)

    ds_types = [dict(x) for x in d_type["sub_types"]]
    for ds_type in ds_types:
        add_ds_type_if_missing(db, ds_type, db_entry.id)


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # BaseTable.metadata.create_all(bind=engine)

    admin = crud.user.get_by_email(db, email=settings.ADMIN_USER)
    if not admin:
        user_in = schemas.UserCreateOut(
            email=settings.ADMIN_USER,
            secret=settings.ADMIN_USER_SECRET,
            is_admin=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841

    # Add disaster types and sub types
    # see https://emergency.copernicus.eu/mapping/ems/domains#_ftnref1
    path = Path(__file__).parent.absolute()
    with open(f'{path}/init_data/d_types.json', 'r') as d_type_file:
        d_types = json.load(d_type_file)

    # convert objects to dict to get .keys(), .values() and .items() functions
    d_types = [dict(x) for x in d_types]
    for d_type in d_types:
        add_d_type_if_missing(db, d_type)


if __name__ == '__main__':
    import logging
    from app.db.session import SessionLocal, engine

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Creating initial data")
    db_session = SessionLocal()
    init_db(db_session)
    logger.info("Initial data created")
