import json

from sqlalchemy.orm import Session

from app import crud
from app.backend.base import BaseProcessor
from app.schemas import ORSRequest, PathOptions, ORSResponse, OrsResponseType


class ORSProcessor(BaseProcessor):
    def handle_ors_request(self, db: Session, request: ORSRequest, options: PathOptions,
                           header_authorization: str = "") -> ORSResponse:
        # process request
        disaster_areas = {}
        lookup_bbox = self.get_bounding_box(request)
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

        # prepare data for relay request
        request_dict = self.prepare_request_dic(request)

        # prepare header for relay request
        request_header = self.prepare_headers(request_dict, options.ors_response_type, header_authorization)

        # debug mode: return modified request without relaying to backend
        if request.portal_options.debug:
            return ORSResponse(body=json.dumps(request_dict), header_type="application/json;charset=UTF-8")

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

        return ORSResponse(body=response_body, header_type=response.headers.get("Content-Type"))

    @staticmethod
    def get_bounding_box(request: ORSRequest) -> list:
        bbox = [
            float(min(c[0] for c in request.coordinates)),
            float(min(c[1] for c in request.coordinates)),
            float(max(c[0] for c in request.coordinates)),
            float(max(c[1] for c in request.coordinates))
        ]
        if request.portal_options.bounds_looseness:
            looseness_factor = int(request.portal_options.bounds_looseness) / 100 / 2
            leeway = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) * looseness_factor
            bbox = [
                round(bbox[0] - leeway, 6),
                round(bbox[1] - leeway, 6),
                round(bbox[2] + leeway, 6),
                round(bbox[3] + leeway, 6)
            ]
        return bbox

    @staticmethod
    def prepare_request_dic(request: ORSRequest) -> dict:
        request_dict = request.dict()
        request_dict.pop("portal_options")
        if len(request.options.avoid_polygons.coordinates) == 0:
            request_dict.get("options").pop("avoid_polygons")
        if len(request_dict.get("options")) == 0:
            request_dict.pop("options")
        return request_dict

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
