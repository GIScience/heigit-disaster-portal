import json
from sqlalchemy.orm import Session
from app import crud
from app.schemas import CustomSpeedsUpdate
from app.schemas.custom_speeds import CustomSpeedsProperties
from app.tests.utils.custom_speeds import create_new_custom_speeds


def test_create_custom_speeds(db: Session) -> None:
    name = "Example custom speeds object entry"
    desc = "A sample custom speeds object with a few random settings"
    created = create_new_custom_speeds(db, name, desc)
    assert created.name == name
    assert created.description == desc
    assert created.content == '{"unit": "kmh", "roadSpeeds": {"motorway": 0, "trunk": 0}, "surfaceSpeeds": {"paved": 0, "concrete:lanes": 50, "gravel": 75}}'
    assert created.id


def test_get_custom_speeds_by_id(db: Session) -> None:
    cs = create_new_custom_speeds(db)
    cs_get = crud.custom_speeds.get(db, cs_id=cs.id)
    assert cs.name == cs_get.properties.name


def test_get_custom_speeds_by_name(db: Session) -> None:
    cs = create_new_custom_speeds(db)
    cs_get = crud.custom_speeds.get_by_name(db, name=cs.name)
    assert cs.id == cs_get.id


def test_get_custom_speeds(db: Session) -> None:
    cs1 = create_new_custom_speeds(db)
    cs1 = crud.custom_speeds.get(db, cs_id=cs1.id)
    cs2 = create_new_custom_speeds(db)
    cs2 = crud.custom_speeds.get(db, cs_id=cs2.id)
    css = crud.custom_speeds.get_multi(db)
    assert cs1 in css
    assert cs2 in css
    for cs in [dict({"name": x.properties.name, "a_id": x.id}) for x in css]:
        assert cs.get("name")
        assert cs.get("a_id")


def test_update_custom_speeds_properties(db: Session) -> None:
    cs = create_new_custom_speeds(db)
    cs = crud.custom_speeds.get(db, cs_id=cs.id)
    cs_update = dict({"properties": {
        "description": "Updated description"
    }})
    cs2 = crud.custom_speeds.update(db, cs_id=cs.id, obj_in=cs_update)
    assert cs2.id == cs.id
    assert cs2.description == cs_update["properties"]["description"]


def test_update_custom_speeds_content(db: Session) -> None:
    cs = create_new_custom_speeds(db)
    cs_update = CustomSpeedsUpdate(
        content=json.loads('{"unit": "kmh", "roadSpeeds": {"motorway": 50, "trunk": 50}, "surfaceSpeeds": {"paved": 10, "concrete:lanes": 20, "gravel": 20}}'),
        properties=CustomSpeedsProperties(
            name=cs.provider_id,
            provider_id=cs.provider_id,
        )
    )
    cs2 = crud.custom_speeds.update(db, cs_id=cs.id, obj_in=cs_update)
    assert cs2 == cs
    assert cs2.content == '{"unit": "kmh", "roadSpeeds": {"motorway": 50, "trunk": 50}, "surfaceSpeeds": {"paved": 10, "concrete:lanes": 20, "gravel": 20}}'


def test_remove_custom_speeds(db: Session) -> None:
    cs = create_new_custom_speeds(db)
    cs_2 = crud.custom_speeds.remove(db, id=cs.id)
    no_cs = crud.provider.get(db, id=cs_2.id)
    assert cs == cs_2
    assert not no_cs
