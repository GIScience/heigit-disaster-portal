from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserCreateOut, UserCreateFromDb
from .base import CRUDBase
from ..security import generate_hash


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_secret(self, db: Session, *, secret: str) -> Optional[User]:
        return db.query(User).filter(User.hashed_secret == generate_hash(secret)).first()

    def is_admin(self, user_obj: User) -> bool:
        return user_obj.is_admin

    def is_active(self, user_obj: User) -> bool:
        return user_obj.is_active

    def create(self, db: Session, *, obj_in: UserCreateOut) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_secret=generate_hash(obj_in.secret),
            is_active=True,
            is_admin=obj_in.is_admin
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_from_db_entry(self, db: Session, *, obj_in: UserCreateFromDb) -> User:
        db_obj = User(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
            self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("secret"):
            hashed_secret = generate_hash(update_data["secret"])
            del update_data["secret"]
            update_data["hashed_secret"] = hashed_secret
        return super().update(db, db_obj=db_obj, obj_in=update_data)


user = CRUDUser(User)
