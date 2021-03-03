from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry, func
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import validates

from app.db.base import BaseTable


class CustomSpeeds(BaseTable):
    __tablename__ = "custom_speeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    created = Column(DateTime, index=True)
    content = Column(String, index=False)
