from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import BaseTable

if TYPE_CHECKING:
    from .disaster_sub_type import DisasterSubType  # noqa: F401


class DisasterType(BaseTable):
    __tablename__ = "disaster_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, index=True)

    sub_types = relationship("DisasterSubType", back_populates="parent")
