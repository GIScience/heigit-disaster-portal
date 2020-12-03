from typing import Optional

from app.models.disaster_type import DisasterType
from app.schemas.disaster_type import DisasterTypeCreate, DisasterTypeUpdate
from sqlalchemy.orm import Session

from .base import CRUDBase


class CRUDDisasterType(CRUDBase[DisasterType, DisasterTypeCreate, DisasterTypeUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[DisasterType]:
        return db.query(DisasterType).filter(DisasterType.name == name).first()


disaster_type = CRUDDisasterType(DisasterType)
