import json
from datetime import datetime
from typing import Union, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models import CustomSpeeds
from app.schemas import CustomSpeeds as CustomSpeedsSchema, CustomSpeedsCreate, CustomSpeedsUpdate
from .base import CRUDBase


class CRUDCustomSpeeds(CRUDBase[CustomSpeedsSchema, CustomSpeedsCreate, CustomSpeedsUpdate]):
    def get(self, db: Session, id: Any) -> Optional[CustomSpeedsSchema]:
        entry = db.query(CustomSpeeds).get(id)
        return entry

    def get_by_name(self, db: Session, *, name: str) -> Optional[CustomSpeedsSchema]:
        return db.query(CustomSpeeds).filter(CustomSpeeds.name == name).first()

    def create(self, db: Session, *, obj_in: CustomSpeedsCreate) -> CustomSpeedsSchema:
        db_obj = CustomSpeeds(
            name=obj_in.properties.name,
            description=obj_in.properties.description,
            provider_id=obj_in.properties.provider_id,
            created=datetime.now(),
            content=json.dumps(obj_in.content),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: CustomSpeeds, obj_in: Union[CustomSpeedsUpdate, Dict[str, Any]]
               ) -> CustomSpeedsSchema:
        if isinstance(obj_in, CustomSpeedsUpdate):
            obj_in = obj_in.dict(exclude_unset=True)
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
