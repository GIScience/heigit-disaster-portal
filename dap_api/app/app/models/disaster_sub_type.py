from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import BaseTable

if TYPE_CHECKING:
    from .disaster_type import DisasterType  # noqa: F401


class DisasterSubType(BaseTable):
    __tablename__ = "disaster_sub_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey("disaster_types.id"))

    parent = relationship("DisasterType", back_populates="sub_types")
