from typing import TYPE_CHECKING

from app.db.base import BaseTable
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from .user import User # noqa


class Provider(BaseTable):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    email = Column(String, unique=True, index=True)
    description = Column(String, index=True)

    owner = relationship("User", back_populates="providers")
