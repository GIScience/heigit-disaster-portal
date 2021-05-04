import json
from datetime import datetime
from typing import Union, Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models import CustomSpeeds
from app.schemas import CustomSpeeds as CustomSpeedsSchema, CustomSpeedsOut, CustomSpeedsCreate, CustomSpeedsUpdate
from .base import CRUDBase
from ..schemas.custom_speeds import CustomSpeedsPropertiesOut


def convert_custom_speeds(db_cs: CustomSpeeds):
    if not db_cs:
        return None
    return CustomSpeedsOut(
        id=db_cs.id,
        content=json.loads(db_cs.content),
        properties=CustomSpeedsPropertiesOut(
            name=db_cs.name,
            description=db_cs.description,
            provider_id=db_cs.provider_id,
            created=db_cs.created
        )
    )


class CRUDCustomSpeeds(CRUDBase[CustomSpeedsSchema, CustomSpeedsCreate, CustomSpeedsUpdate]):
    def get(self, db: Session, cs_id: Any) -> Optional[CustomSpeedsOut]:
        entry = db.query(CustomSpeeds).get(cs_id)
        return convert_custom_speeds(entry)

    def get_multi(
            self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[CustomSpeedsOut]:
        res = super().get_multi(db=db, skip=skip, limit=limit)
        return [convert_custom_speeds(cs) for cs in res]

    @staticmethod
    def get_by_name(db: Session, *, name: str) -> Optional[CustomSpeedsSchema]:
        return db.query(CustomSpeeds).filter(CustomSpeeds.name == name).first()

    def create(self, db: Session, *, obj_in: CustomSpeedsCreate) -> CustomSpeeds:
        db_obj = CustomSpeeds(
            name=obj_in.properties.name,
            description=obj_in.properties.description,
            provider_id=obj_in.properties.provider_id,
            created=datetime.now(),
            content=obj_in.content.json(by_alias=True, exclude_unset=True),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, cs_id: CustomSpeeds, obj_in: Union[CustomSpeedsUpdate, Dict[str, Any]]
               ) -> CustomSpeedsOut:
        db_obj = db.query(CustomSpeeds).get(cs_id)
        if isinstance(obj_in, CustomSpeedsUpdate):
            obj_in = obj_in.dict(exclude_unset=True, by_alias=True)
        if obj_in.get('content'):
            setattr(db_obj, 'content', json.dumps(obj_in.get('content')))
            del obj_in['content']
        update_data = obj_in
        if update_data.get('properties'):
            update_data = update_data['properties']
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


custom_speeds = CRUDCustomSpeeds(CustomSpeeds)
