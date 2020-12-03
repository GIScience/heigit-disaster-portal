from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.provider import Provider
from app.schemas.provider import ProviderCreate, ProviderUpdate
from .base import CRUDBase


class CRUDProvider(CRUDBase[Provider, ProviderCreate, ProviderUpdate]):
    def get_multi_by_owner(
            self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Provider]:
        return (
            db.query(self.model)
                .filter(Provider.owner_id == owner_id)
                .offset(skip)
                .limit(limit)
                .all()
        )

    def get_by_email(self, db: Session, *, email: str) -> Optional[Provider]:
        return db.query(Provider).filter(Provider.email == email).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Provider]:
        return db.query(Provider).filter(Provider.name == name).first()


provider = CRUDProvider(Provider)
