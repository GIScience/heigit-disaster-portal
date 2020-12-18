"""
Reusable dependencies that are injected into different endpoints
"""
from typing import List, Optional

from fastapi import Query, HTTPException, Header
from pydantic import ValidationError

from app.db.session import SessionLocal
from app.schemas.disaster_area import BBoxModel


# Dependency
def get_db():  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_valid_bbox(bbox: Optional[List[str]] = Query(
    ["-180., -90., 180., 90"],
    title="Bbox",
    description="""
Bounding box to request features in, as comma separated float values west(lon), south(lat), east(lon), north(lat).

Can also be passed in this order in separate query parameter instances like
`?bbox=west&bbox=south&bbox=east&bbox=north`.

**Contrary to the specified bbox array type, float values need to be passed instead of a string!**
"""
)
):
    if len(bbox) != 4:
        bbox = [float(x) for x in bbox[0].split(',')]
    try:
        bbox_obj = BBoxModel.parse_obj(bbox)
    except ValidationError as e:
        for error in e.errors():
            error['loc'] = ["query", "bbox"]
        raise HTTPException(
            status_code=422,
            detail=e.errors()
        )
    return bbox_obj


def common_multi_query_params(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1)
):
    return {"skip": skip, "limit": limit}


def ors_api_key_param(api_key: str = Query(None)):
    if not api_key:
        raise HTTPException(status_code=400, detail="Openrouteservice api key missing in api_key parameter")
    return api_key


def ors_auth_header(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=400, detail="Openrouteservice api key missing in authorization header")
    return authorization
