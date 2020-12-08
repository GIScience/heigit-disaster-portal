from typing import Optional

from app.models.disaster_sub_type import DisasterSubType
from app.schemas.disaster_sub_type import DisasterSubTypeCreate, DisasterSubTypeUpdate
from sqlalchemy.orm import Session

from .base import CRUDBase


class CRUDDisasterSubType(CRUDBase[DisasterSubType, DisasterSubTypeCreate, DisasterSubTypeUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[DisasterSubType]:
        return db.query(DisasterSubType).filter(DisasterSubType.name == name).first()

    def create(self, db: Session, *, obj_in: DisasterSubTypeCreate) -> DisasterSubType:
        db_obj = DisasterSubType(
            name=obj_in.name,
            description=obj_in.description,
            parent_id=obj_in.parent_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


disaster_sub_type = CRUDDisasterSubType(DisasterSubType)
