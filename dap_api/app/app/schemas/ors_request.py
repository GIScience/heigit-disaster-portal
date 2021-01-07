from enum import Enum
from typing import Optional

from pydantic import BaseModel, Extra, conint, conlist


class PortalMode(str, Enum):
    avoid_area = "avoid_areas"


class OrsApi(str, Enum):
    directions = "directions",


class OrsProfile(str, Enum):
    driving_car = "driving-car"
    driving_hgv = "driving-hgv"


class OrsResponseType(str, Enum):
    json = "json"
    geojson = "geojson"
    gpx = "gpx"


class PortalOptions(BaseModel):
    debug: Optional[bool] = False
    return_areas_in_response: Optional[bool] = False
    bounds_looseness: Optional[conint(ge=0, le=200)] = 0


class AvoidPolygons(BaseModel):
    coordinates: conlist(list, min_items=1) = []
    type: str = "MultiPolygon"


class Options(BaseModel):
    avoid_polygons: Optional[AvoidPolygons] = AvoidPolygons()

    class Config:
        extra = Extra.allow


class PathOptionsValidation:
    def __init__(
            self,
            portal_mode: PortalMode = "avoid_areas",
            ors_api: OrsApi = "directions",
            ors_profile: OrsProfile = "driving-car",
    ):
        self.portal_mode = portal_mode
        self.ors_api = ors_api
        self.ors_profile = ors_profile

    def __dict__(self):
        return dict(
            {
                "portal_mode": self.portal_mode,
                "ors_api": self.ors_api,
                "ors_profile": self.ors_profile
            }
        )

    def dict(self):
        return self.__dict__()


class PathOptions(BaseModel):
    portal_mode: PortalMode
    ors_api: OrsApi
    ors_profile: OrsProfile
    ors_response_type: OrsResponseType


class ORSRequest(BaseModel):
    portal_options: Optional[PortalOptions] = PortalOptions()
    options: Optional[Options] = Options()
    coordinates: conlist(list, min_items=1)

    class Config:
        extra = Extra.allow


class ORSResponse(BaseModel):
    status_code: int
    body: str
    header_type: str
