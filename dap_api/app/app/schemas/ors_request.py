from enum import Enum
from typing import Optional

from dateutil.parser import isoparse
from pydantic import BaseModel, Extra, conint, conlist, Field, validator

from app.schemas import CustomSpeedsContent
from app.schemas.disaster_area import BBoxModel
from app.schemas.utils import ISO_EXAMPLES, DIR_EXAMPLES, BASE_EXAMPLE, datetime_parameter, D_ID_LOOKUP


class PortalMode(str, Enum):
    avoid_area = "avoid_areas"
    custom_speeds = "custom_speeds"


class OrsApi(str, Enum):
    directions = "directions"
    isochrones = "isochrones"


class OrsProfile(str, Enum):
    driving_car = "driving-car"
    driving_hgv = "driving-hgv"
    cycling_regular = "cycling-regular"
    cycling_mountain = "cycling-mountain"
    cycling_road = "cycling-road"
    cycling_electric = "cycling-electric"
    foot_walking = "foot-walking"
    foot_hiking = "foot-hiking"
    wheelchair = "wheelchair"


class OrsResponseType(str, Enum):
    json = "json"
    geojson = "geojson"
    gpx = "gpx"


class OrsIsochroneRangeType(str, Enum):
    time = "time"
    distance = "distance"


class DisasterAreaFilter(BaseModel):
    bbox: BBoxModel | None = Field(
        default=None,
        title='Bounding Box',
        description='Bounding box as comma separated float values west(lon), south(lat), '
                    'east(lon), north(lat). Only features which intersect this bbox are used.'
    )
    date_time: str | None = Field(**datetime_parameter)
    d_type_id: int | None = Field(
        default=None,
        title='Disaster type ID',
        description='ID of a specific disaster type. Only features with this disaster type ID are used'
    )

    @validator("date_time")
    def check_date_time(cls, value):
        if value is None:
            return value
        date_time_array = value.split('/')
        if len(date_time_array) == 1:
            try:
                isoparse(value)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp {value}: {e}")
        elif len(date_time_array) == 2:
            date1, date2 = date_time_array
            if date1 not in ['', '..']:
                try:
                    isoparse(date1)
                except ValueError as e:
                    raise ValueError(f"Invalid stop timestamp {date1}: {e}")
            if date2 not in ['', '..']:
                try:
                    isoparse(date2)
                except ValueError as e:
                    raise ValueError(f"Invalid stop timestamp {date2}: {e}")
        return value

    @validator("d_type_id")
    def check_d_type(cls, value):
        if value not in D_ID_LOOKUP:
            raise ValueError(f"Invalid d_type_id '{value}'. A disaster type with this id does not exists.")
        return value


class PortalOptions(BaseModel):
    debug: Optional[bool] = False
    return_areas_in_response: Optional[bool] = False
    bounds_looseness: Optional[conint(ge=0, le=200)] = 0
    generate_difference: Optional[bool] = Field(False, description='Generates difference between requests with and '
                                                                   'without avoid areas. Uses up 2 ORS requests.')
    disaster_area_filter: DisasterAreaFilter | None = DisasterAreaFilter()
    ors_server: str | None = None


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
    user_speed_limits: Optional[int | CustomSpeedsContent] = Field(
        None,
        description='Either the ID of a `custom_speeds` set from the storage or an object following the '
                    'CustomSpeedsContent schema')

    class Config:
        extra = Extra.allow
        schema_extra = {
            "examples": BASE_EXAMPLE
        }


class ORSIsochrones(ORSRequest):
    locations: conlist(list, min_items=1)
    range: conlist(float, min_items=1)
    range_type: Optional[OrsIsochroneRangeType]

    class Config:
        schema_extra = {
            "examples": ISO_EXAMPLES
        }


class ORSDirections(ORSRequest):
    coordinates: conlist(list, min_items=1)

    class Config:
        schema_extra = {
            "examples": DIR_EXAMPLES
        }


class ORSResponse(BaseModel):
    status_code: int
    body: str
    media_type: str
