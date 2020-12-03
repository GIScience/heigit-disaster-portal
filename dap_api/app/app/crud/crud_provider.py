from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from . import user
from .base import CRUDBase
from app.models.provider import Provider
from app.schemas.provider import ProviderCreate, ProviderUpdate, ProviderCreateOut


class CRUDProvider(CRUDBase[Provider, ProviderCreate, ProviderUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Provider]:
        return db.query(Provider).filter(Provider.email == email).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Provider]:
        return db.query(Provider).filter(Provider.name == name).first()

    def create(self, db: Session, *, obj_in: ProviderCreateOut) -> Provider:
        db_obj = Provider(
            email=obj_in.email,
            name=obj_in.name,
            description=obj_in.description,
            owner_id=obj_in.owner_id,
            owner=user.get(db, obj_in.owner_id)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


provider = CRUDProvider(Provider)
