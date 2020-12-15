from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry, func
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import validates

from app.db.base import BaseTable

if TYPE_CHECKING:
    from .disaster_type import DisasterType  # noqa: F401


class DisasterArea(BaseTable):
    __tablename__ = "disaster_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    d_type_id = Column(Integer, ForeignKey("disaster_types.id"), nullable=False)
    ds_type_id = Column(Integer, ForeignKey("disaster_sub_types.id"))
    description = Column(String, index=True)
    created = Column(DateTime, index=True)
    area = Column(Float, index=True)

    geom = Column(Geometry('POLYGON', srid=4326))

    @validates("geom")
    def validate_geometry(self, key, geom):
        from app.db.session import SessionLocal
        db = SessionLocal()
        valid_check = db.query(func.ST_IsValidReason(geom)).first()[0]
        if valid_check != "Valid Geometry":
            raise ValueError(f"Invalid geometry: {valid_check}")
        return geom
