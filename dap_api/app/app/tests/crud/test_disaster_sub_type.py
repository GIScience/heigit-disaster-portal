from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.models import DisasterSubType
from app.schemas.disaster_sub_type import DisasterSubTypeCreate, DisasterSubTypeUpdate
from app.tests.crud.test_disaster_type import create_new_disaster_type
from app.tests.utils.utils import random_lower_string


def create_new_ds_type(db: Session) -> DisasterSubType:
    d_type = create_new_disaster_type(db)
    name = random_lower_string(8)
    info = random_lower_string()
    disaster_sub_type_in = DisasterSubTypeCreate(name=name, description=info, parent_id=d_type.id)
    return crud.disaster_sub_type.create(db, obj_in=disaster_sub_type_in)


def test_create_disaster_sub_type(db: Session) -> None:
    d_type = create_new_disaster_type(db)
    name = random_lower_string(8)
    info = random_lower_string()
    disaster_sub_type_in = DisasterSubTypeCreate(name=name, description=info, parent_id=d_type.id)
    disaster_sub_type = crud.disaster_sub_type.create(db, obj_in=disaster_sub_type_in)
    assert disaster_sub_type.name == name
    assert disaster_sub_type.description == info
    assert disaster_sub_type.id


def test_get_disaster_sub_type(db: Session) -> None:
    ds_type = create_new_ds_type(db)
    disaster_sub_type_out = crud.disaster_sub_type.get(db, id=ds_type.id)
    assert disaster_sub_type_out
    assert ds_type.name == disaster_sub_type_out.name
    assert ds_type.description == disaster_sub_type_out.description
    assert ds_type.parent_id == disaster_sub_type_out.parent_id
    assert jsonable_encoder(ds_type) == jsonable_encoder(disaster_sub_type_out)


def test_get_disaster_sub_type_by_name(db: Session) -> None:
    ds_type = create_new_ds_type(db)
    disaster_sub_type_2 = crud.disaster_sub_type.get_by_name(db, name=ds_type.name)
    assert disaster_sub_type_2
    assert ds_type.description == disaster_sub_type_2.description
    assert jsonable_encoder(ds_type) == jsonable_encoder(disaster_sub_type_2)


def test_update_disaster_sub_type(db: Session) -> None:
    ds_type = create_new_ds_type(db)
    new_info = "New info"
    disaster_sub_type_update = DisasterSubTypeUpdate(description=new_info)
    disaster_sub_type_2 = crud.disaster_sub_type.update(db, db_obj=ds_type, obj_in=disaster_sub_type_update)
    assert disaster_sub_type_2.name == ds_type.name
    assert disaster_sub_type_2.id == ds_type.id
    assert disaster_sub_type_2.description == new_info


def test_remove_disaster_sub_type(db: Session) -> None:
    ds_type = create_new_ds_type(db)
    ds_type_rm = crud.disaster_sub_type.remove(db, id=ds_type.id)
    no_ds_type = crud.disaster_sub_type.get(db, id=ds_type_rm.id)
    assert jsonable_encoder(ds_type_rm) == jsonable_encoder(ds_type)
    assert not no_ds_type
