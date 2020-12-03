from typing import Optional

from app.models.disaster_type import DisasterType
from app.schemas.disaster_type import DisasterTypeCreate, DisasterTypeUpdate
from sqlalchemy.orm import Session

from .base import CRUDBase


class CRUDUser(CRUDBase[DisasterType, DisasterTypeCreate, DisasterTypeUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[DisasterType]:
        return db.query(DisasterType).filter(DisasterType.name == name).first()

    def create(self, db: Session, *, obj_in: DisasterTypeCreate) -> DisasterType:
        db_obj = DisasterType(
            name=obj_in.name,
            description=obj_in.description
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


disaster_type = CRUDUser(DisasterType)
