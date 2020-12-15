import json
from datetime import datetime
from typing import Union, Dict, Any, Optional, List

from geoalchemy2 import func, Geometry
from geojson_pydantic.geometries import Polygon
from geojson_pydantic.utils import BBox
from sqlalchemy.orm import Session

from app.models import DisasterArea
from app.schemas import DisasterArea as DisasterAreaSchema
from app.schemas import DisasterAreaCreate, DisasterAreaUpdate
from .base import CRUDBase
from ..schemas.disaster_area import DisasterAreaPropertiesCreateOut, DisasterAreaCollection


def get_entry_as_feature(db: Session, entry: DisasterArea) -> DisasterAreaSchema:
    json_geom = json.loads(db.execute(entry.geom.ST_AsGeoJson(9, 1)).scalar())
    d_area = DisasterAreaSchema(
        id=entry.id,
        properties=DisasterAreaPropertiesCreateOut(**entry.__dict__),
        geometry=Polygon(**json_geom),
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
            self, db: Session, bbox: BBox = None, skip: int = 0, limit: int = 100
    ) -> List[DisasterArea]:
        if bbox:
            query_list = db.query(DisasterArea).filter(
                DisasterArea.geom.intersects(func.ST_MakeEnvelope(*bbox))
            ).offset(skip).limit(limit).all()
            return query_list
        return super().get_multi(db=db, skip=skip, limit=limit)

    def get_multi_as_feature_collection(
            self, db: Session, bbox: BBox = None, skip: int = 0, limit: int = 100
    ) -> DisasterAreaCollection:
        entries = self.get_multi(db, bbox, skip, limit)
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
        geom = func.ST_GeomFromGeoJSON(obj_in.geometry.json())
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

    def update(self, db: Session, *, db_obj: DisasterArea, obj_in: Union[DisasterAreaUpdate, Dict[str, Any]]
               ) -> DisasterArea:
        if isinstance(obj_in, DisasterAreaUpdate):
            obj_in = obj_in.dict(exclude_unset=True)
        if obj_in.get('geometry'):
            geom = func.ST_GeomFromGeoJSON(json.dumps(obj_in.get('geometry')))
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
