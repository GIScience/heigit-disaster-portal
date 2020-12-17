from typing import Optional

from pydantic import BaseModel, Extra


class PortalOptions(BaseModel):
    debug: Optional[bool] = False
    return_areas_in_response: Optional[bool] = False


class AvoidPolygons(BaseModel):
    coordinates: Optional[list] = []
    type: str = "MultiPolygon"


class Options(BaseModel):
    avoid_polygons: Optional[AvoidPolygons] = AvoidPolygons()

    class Config:
        extra = Extra.allow


class PathOptions(BaseModel):
    portal_mode: str
    ors_api: str
    ors_profile: str
    ors_response_type: str


class ORSRequest(BaseModel):
    portal_options: Optional[PortalOptions] = PortalOptions()
    options: Optional[Options] = Options()
    coordinates: Optional[list] = []

    class Config:
        extra = Extra.allow


class ORSResponse(BaseModel):
    body: str
    header_type: str
