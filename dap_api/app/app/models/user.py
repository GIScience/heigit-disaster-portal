from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String

from app.db.base import BaseTable
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from .provider import Provider  # noqa: F401


class User(BaseTable):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_secret = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    providers = relationship("Provider", back_populates="owner")
