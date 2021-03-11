import json
from typing import Union

from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from app import crud
from app.backend.base import BaseProcessor
from app.schemas import ORSRequest, PathOptions, ORSResponse
from app.backend.geoutil import bbox_buffer_percentage, meters_travelled, bbox_from_radius


class ORSProcessor(BaseProcessor):
    def handle_ors_request(self, db: Session, request: ORSRequest, options: PathOptions,
                           header_authorization: str = "") -> Union[ORSResponse, JSONResponse]:
        # process request
        disaster_areas = {}
        lookup_bbox = self.get_bounding_box(request, options.ors_api, options.ors_profile)
        if options.portal_mode.value == "avoid_areas":
            disaster_areas = crud.disaster_area.get_multi_as_feature_collection(db, lookup_bbox)
            coordinates_to_add = [f.geometry.coordinates for f in disaster_areas.features if
                                  f.geometry.type in ["Polygon"]]
            if coordinates_to_add:
                # ORS expects Polygon coordinates to be a list of lists of coordinates, whilst for MultiPolygon
                # coordinates is expected to be a list of lists of lists of coordinates. If we get a Polygon in the
                # original request, we need to convert it to a MultiPolygon before adding
                if request.options.avoid_polygons.type == "Polygon":
                    request.options.avoid_polygons.type = "MultiPolygon"
                    request.options.avoid_polygons.coordinates = [request.options.avoid_polygons.coordinates]
                request.options.avoid_polygons.coordinates += coordinates_to_add

        if type(request.user_speed_limits) == int:
            cs = crud.custom_speeds.get(db, request.user_speed_limits)
            if not cs:
                return JSONResponse(status_code=400, content={
                    "code": 6404,
                    "message": "A Custom speeds entry with the given ID does not exist."
                })
            request.user_speed_limits = cs.content

        # prepare relay request
        request_dict = self.prepare_request_dic(request)
        request_header = self.prepare_headers(request_dict, options.ors_response_type.value, header_authorization)

        # debug mode: return modified request without relaying to backend
        if request.portal_options.debug:
            return ORSResponse(
                status_code=200,
                body=json.dumps(request_dict),
                media_type="application/json;charset=UTF-8"
            )

        # relay to backend
        endpoint = f"/{options.ors_api}/{options.ors_profile}/{options.ors_response_type}"
        response = self.relay_request_post(endpoint, request_header, request_dict)

        # process result
        if options.ors_response_type.value == "gpx":
            response_body = response.text
        else:
            response_json = response.json()
            if request.portal_options.return_areas_in_response:
                response_json["disaster_areas"] = json.loads(disaster_areas.json())
                response_json["disaster_areas_lookup_bbox"] = lookup_bbox
            response_body = json.dumps(response_json)

        return ORSResponse(
            status_code=response.status_code,
            body=response_body,
            media_type=response.headers.get("Content-Type")
        )

    @staticmethod
    def get_bounding_box(request: ORSRequest, target_api, target_profile) -> list:
        bbox = [0, 0, 0, 0]

        if target_api == "directions":
            bbox = [
                float(min(c[0] for c in request.coordinates)),
                float(min(c[1] for c in request.coordinates)),
                float(max(c[0] for c in request.coordinates)),
                float(max(c[1] for c in request.coordinates))
            ]
            if request.portal_options.bounds_looseness and int(request.portal_options.bounds_looseness) > 0:
                bbox = bbox_buffer_percentage(bbox, int(request.portal_options.bounds_looseness))

        if target_api == "isochrones":
            # this is a quick and dirty solution, it would be more efficient to do point-radius lookups in the database
            # directly. A TODO for the production version.
            radius = max(request.range)
            if request.range_type is None or request.range_type == "time":
                # range is seconds of travel time, convert to distance
                speed = 80  # default to car
                if target_profile.startswith("cycling"):
                    speed = 20
                if target_profile.startswith("foot"):
                    speed = 5
                if target_profile.startswith("wheelchair"):
                    speed = 4
                radius = meters_travelled(radius, speed)
            boxes = []
            for point in request.locations:
                boxes.append(bbox_from_radius(point[0], point[1], radius))
            bbox = [
                float(min(b[0] for b in boxes)),
                float(min(b[1] for b in boxes)),
                float(max(b[2] for b in boxes)),
                float(max(b[3] for b in boxes))
            ]
        return bbox

    @staticmethod
    def fix_bbox(bbox):
        return bbox

    @staticmethod
    def prepare_request_dic(request: ORSRequest) -> dict:
        request_dict = request.dict()
        request_dict.pop("portal_options")
        request_dict = clean_dict(request_dict)
        if "options" in request_dict:
            if len(request.options.avoid_polygons.coordinates) == 0:
                request_dict.get("options").pop("avoid_polygons")
            if len(request_dict.get("options")) == 0:
                request_dict.pop("options")
        return request_dict

    @staticmethod
    def prepare_headers(request_dict: dict, response_type: str, header_authorization: str) -> dict:
        request_header = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        if response_type == "gpx":
            request_header["Accept"] = "application/gpx+xml"
        elif response_type == "geojson":
            request_header["Accept"] = "application/geo+json"
        else:
            request_header["Accept"] = "application/json"
        if "api_key" in request_dict:
            request_header["Authorization"] = request_dict.pop("api_key")
        if len(header_authorization) > 0:
            request_header["Authorization"] = header_authorization
        return request_header


def clean_dict(d):
    clean = {}
    for k, v in d.items():
        if isinstance(v, dict):
            nested = clean_dict(v)
            if len(nested.keys()) > 0:
                clean[k] = nested
        elif v is not None:
            clean[k] = v
    return clean
