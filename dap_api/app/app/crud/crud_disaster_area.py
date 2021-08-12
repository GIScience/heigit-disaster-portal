import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from dateutil import parser as date_parser
from geoalchemy2 import func, Geometry
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import DisasterArea
from app.schemas import DisasterArea as DisasterAreaSchema
from app.schemas import DisasterAreaCreate, DisasterAreaUpdate
from .base import CRUDBase
from ..schemas.disaster_area import DisasterAreaCollection, BBoxModel


def multi_to_single(multi_polygon: dict) -> None:
    multi_polygon.update(type="Polygon", coordinates=multi_polygon.get("coordinates")[0])


def single_to_multi(polygon: dict) -> None:
    polygon.update(type="MultiPolygon", coordinates=[polygon.get("coordinates")])


def get_entry_as_feature(db: Session, entry: DisasterArea) -> DisasterAreaSchema:
    json_geom = json.loads(db.execute(entry.geom.ST_AsGeoJson(7, 1)).scalar())
    if len(json_geom.get("coordinates")) == 1:
        multi_to_single(json_geom)
    d_area = DisasterAreaSchema(
        id=entry.id,
        properties=entry.__dict__,
        geometry=json_geom,
        bbox=json_geom.get('bbox')
    )
    return d_area


def calculate_geometry_area(db: Session, geom: Geometry) -> float:
    # get the best Projection for area calculation
    best_area_projection = db.execute(func._ST_BestSRID(geom)).scalar()
    # reproject to
    transformed_geom = func.ST_Transform(geom, best_area_projection)
    # calculate polygon area
    area = db.execute(func.ST_Area(transformed_geom)).scalar()
    return round(area, 2)


class CRUDDisasterArea(CRUDBase[DisasterArea, DisasterAreaCreate, DisasterAreaUpdate]):
    def get(self, db: Session, id: Any) -> Optional[DisasterArea]:
        entry = db.query(DisasterArea).get(id)
        return entry

    def get_as_feature(self, db: Session, id: Any) -> Optional[DisasterAreaSchema]:
        entry = db.query(DisasterArea).get(id)
        d_area = get_entry_as_feature(db, entry)
        return d_area

    def get_multi(
            self, db: Session, bbox: BBoxModel = None, skip: int = 0, limit: int = 100, d_type_id: int = None,
            date_time: str = None
    ) -> List[DisasterArea]:
        if any([x is not None for x in [bbox, d_type_id, date_time]]):
            query = db.query(DisasterArea)
            if bbox:
                query = query.filter(
                    DisasterArea.geom.intersects(func.ST_MakeEnvelope(*bbox))
                )
            if d_type_id:
                query = query.filter(
                    DisasterArea.d_type_id == d_type_id
                )
            if date_time:
                date_time_array = date_time.split('/')
                if len(date_time_array) == 1:
                    query = query.filter(DisasterArea.created == date_parser.isoparse(date_time))
                elif len(date_time_array) == 2:
                    date1, date2 = date_time_array
                    if date1 not in ['', '..']:
                        query = query.filter(DisasterArea.created >= date_parser.isoparse(date1))
                    if date2 not in ['', '..']:
                        query = query.filter(DisasterArea.created <= date_parser.isoparse(date2))
            return query.order_by(desc(DisasterArea.area)).offset(skip).limit(limit).all()
        return super().get_multi(db=db, skip=skip, limit=limit)

    def get_multi_as_feature_collection(
            self, db: Session, bbox: BBoxModel = None, skip: int = 0, limit: int = 100, d_type_id: int = None,
            date_time: str = None
    ) -> DisasterAreaCollection:
        entries = self.get_multi(db, bbox, skip, limit, d_type_id, date_time)
        features = [self.get_as_feature(db, e.id) for e in entries]
        boxes = [f.bbox for f in features]
        bbox = [0, 0, 0, 0]
        if boxes:
            bbox = [
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes)
            ]
        return DisasterAreaCollection(
            features=features,
            bbox=bbox
        )

    def get_by_name(self, db: Session, *, name: str) -> Optional[DisasterArea]:
        return db.query(DisasterArea).filter(DisasterArea.name == name).first()

    def create(self, db: Session, *, obj_in: DisasterAreaCreate) -> DisasterArea:
        geom_dict = obj_in.geometry.dict()
        if len(obj_in.geometry.coordinates) == 1:
            single_to_multi(geom_dict)
        geom = func.ST_GeomFromGeoJSON(json.dumps(geom_dict))
        area = calculate_geometry_area(db, geom)
        db_obj = DisasterArea(
            name=obj_in.properties.name,
            provider_id=obj_in.properties.provider_id,
            d_type_id=obj_in.properties.d_type_id,
            ds_type_id=obj_in.properties.ds_type_id,
            description=obj_in.properties.description,
            geom=geom,
            area=area,
            created=datetime.now()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: DisasterArea, obj_in: DisasterAreaUpdate | Dict[str, Any]
               ) -> DisasterArea:
        if isinstance(obj_in, DisasterAreaUpdate):
            obj_in = obj_in.dict(exclude_unset=True)
        if obj_in.get('geometry'):
            geom_dict = obj_in.get('geometry')
            if len(geom_dict.get("coordinates")) == 1:
                single_to_multi(geom_dict)
            geom = func.ST_GeomFromGeoJSON(json.dumps(geom_dict))
            area = calculate_geometry_area(db, geom)
            setattr(db_obj, 'geom', geom)
            setattr(db_obj, 'area', area)
            del obj_in['geometry']
        update_data = obj_in
        if update_data.get('properties'):
            update_data = update_data['properties']
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


disaster_area = CRUDDisasterArea(DisasterArea)
