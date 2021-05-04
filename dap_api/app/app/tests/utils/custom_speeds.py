import json
from sqlalchemy.orm import Session
from app import crud
from app.models import CustomSpeeds
from app.schemas import CustomSpeedsCreate, CustomSpeedsProperties
from app.tests.utils.utils import random_lower_string


def create_new_custom_speeds(
        db: Session,
        name: str = None,
        desc: str = None,
        p_id: int = 1,
) -> CustomSpeeds:
    if name is None:
        name = random_lower_string(8)
    if desc is None:
        desc = random_lower_string(16)
    content = json.loads('''{
        "unit": "kmh",
        "roadSpeeds": {
            "motorway": 0,
            "trunk": 0
        },
        "surfaceSpeeds": {
            "paved": 0,
            "concrete:lanes": 50,
            "gravel": 75
        }
    }''')
    cs = CustomSpeedsCreate(
        content=content,
        properties=CustomSpeedsProperties(
            name=name,
            provider_id=p_id,
            description=desc
        )
    )
    return crud.custom_speeds.create(
        db=db,
        obj_in=cs
    )
