import json

from sqlalchemy.orm import Session

from app import crud
from app.backend.base import BaseProcessor
from app.schemas import ORSRequest, PathOptions, ORSResponse, OrsResponseType


class ORSProcessor(BaseProcessor):
    def handle_ors_request(self, db: Session, request: ORSRequest, options: PathOptions,
                           header_authorization: str = "") -> ORSResponse:

        # process request
        disaster_areas = []
        if options.portal_mode.value == "avoid_areas":
            disaster_areas = crud.disaster_area.get_multi_as_feature_collection(db, self.get_bounding_box(request))
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

        # prepare data for relay request
        request_dict = request.dict()
        request_dict.pop("portal_options")
        if len(request.options.avoid_polygons.coordinates) == 0:
            request_dict.get("options").pop("avoid_polygons")
        if len(request_dict.get("options")) == 0:
            request_dict.pop("options")

        # prepare header for relay request
        request_header = self.prepare_headers(request_dict, options.ors_response_type, header_authorization)

        # debug mode: return modified request without relaying to backend
        if request.portal_options.debug:
            return ORSResponse(body=json.dumps(request_dict), header_type="application/json;charset=UTF-8")

        endpoint = f"/{options.ors_api}/{options.ors_profile}/{options.ors_response_type}"
        response = self.relay_request_post(endpoint, request_header, request_dict)

        # process result
        response_body = json.loads(response.text)
        if request.portal_options.return_areas_in_response and len(
                disaster_areas.features) and options.ors_response_type.value != "gpx":
            response_body["disaster_areas"] = json.loads(disaster_areas.json())

        return ORSResponse(body=json.dumps(response_body), header_type=response.headers.get("Content-Type"))

    @staticmethod
    def prepare_headers(request_dict: dict, response_type: OrsResponseType, header_authorization: str) -> dict:
        request_header = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        if response_type.value == "gpx":
            request_header["Accept"] = "application/gpx+xml"
        elif response_type.value == "geojson":
            request_header["Accept"] = "application/geo+json"
        else:
            request_header["Accept"] = "application/json"
        if "api_key" in request_dict:
            request_header["Authorization"] = request_dict.pop("api_key")
        if len(header_authorization) > 0:
            request_header["Authorization"] = header_authorization
        return request_header

    @staticmethod
    def get_bounding_box(request: ORSRequest) -> list:
        return [
            min(c[0] for c in request.coordinates),
            min(c[1] for c in request.coordinates),
            max(c[0] for c in request.coordinates),
            max(c[1] for c in request.coordinates)
        ]
