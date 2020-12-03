from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.models import DisasterType
from app.schemas.disaster_type import DisasterTypeCreate, DisasterTypeUpdate
from app.tests.utils.utils import random_lower_string


def create_new_disaster_type(db) -> DisasterType:
    obj_in = DisasterTypeCreate(name=random_lower_string(8), description=random_lower_string())
    return crud.disaster_type.create(db, obj_in=obj_in)


def test_create_disaster_type(db: Session) -> None:
    name = random_lower_string(8)
    info = random_lower_string()
    disaster_type_in = DisasterTypeCreate(name=name, description=info)
    disaster_type = crud.disaster_type.create(db, obj_in=disaster_type_in)
    assert disaster_type.name == name
    assert disaster_type.description == info
    assert disaster_type.id


def test_get_disaster_type(db: Session) -> None:
    disaster_type = create_new_disaster_type(db)
    disaster_type_out = crud.disaster_type.get(db, id=disaster_type.id)
    assert disaster_type_out
    assert disaster_type.name == disaster_type_out.name
    assert disaster_type.description == disaster_type_out.description
    assert jsonable_encoder(disaster_type) == jsonable_encoder(disaster_type_out)


def test_get_disaster_type_by_name(db: Session) -> None:
    disaster_type = create_new_disaster_type(db)
    disaster_type_2 = crud.disaster_type.get_by_name(db, name=disaster_type.name)
    assert disaster_type_2
    assert disaster_type.description == disaster_type_2.description
    assert jsonable_encoder(disaster_type) == jsonable_encoder(disaster_type_2)


def test_update_disaster_type(db: Session) -> None:
    disaster_type = create_new_disaster_type(db)
    new_info = "New info"
    disaster_type_update = DisasterTypeUpdate(description=new_info)
    disaster_type_2 = crud.disaster_type.update(db, db_obj=disaster_type, obj_in=disaster_type_update)
    assert disaster_type_2.name == disaster_type.name
    assert disaster_type_2.id == disaster_type.id
    assert disaster_type_2.description == new_info


def test_remove_disaster_type(db: Session) -> None:
    disaster_type = create_new_disaster_type(db)
    disaster_type_2 = crud.disaster_type.remove(db, id=disaster_type.id)
    no_disaster_type = crud.disaster_type.get(db, id=disaster_type_2.id)
    assert jsonable_encoder(disaster_type_2) == jsonable_encoder(disaster_type)
    assert not no_disaster_type
