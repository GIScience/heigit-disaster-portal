import json
from typing import Union

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud
from app.backend.base import BaseProcessor
from app.backend.geoutil import bbox_buffer_percentage, meters_travelled, bbox_from_radius, build_diff_query, \
    get_overall_bbox, get_bbox_for_encoded_polyline
from app.schemas import PathOptions, ORSResponse
from app.schemas.ors_request import ORSIsochrones, ORSDirections


class ORSProcessor(BaseProcessor):
    def handle_ors_request(self, db: Session, request: Union[ORSDirections, ORSIsochrones], options: PathOptions,
                           header_authorization: str = "") -> Union[ORSResponse, JSONResponse]:
        # process request
        disaster_areas = {}
        lookup_bbox = self.get_bounding_box(request, options.ors_api, options.ors_profile)
        if options.portal_mode.value == "avoid_areas":
            # TODO: add filters for areas
            disaster_areas = crud.disaster_area.get_multi_as_feature_collection(db, lookup_bbox)
            coordinates_to_add = [f.geometry.coordinates for f in disaster_areas.features if
                                  f.geometry.type in ["Polygon"]]
            if coordinates_to_add:
                # ORS expects Polygon coordinates to be a list of lists of coordinates, whilst for MultiPolygon
                # coordinates is expected to be a list of lists, of lists of coordinates. If we get a Polygon in the
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

        # debug mode: return modified request without relaying to backend TODO: log instead
        if request.portal_options.debug:
            return ORSResponse(
                status_code=200,
                body=json.dumps(request_dict),
                media_type="application/json;charset=UTF-8"
            )

        # relay to backend
        endpoint = f"/{options.ors_api}/{options.ors_profile}/{options.ors_response_type}"
        response = self.relay_request_post(endpoint, request_header, request_dict)
        response_json = {}
        if response.status_code == 200 and request.portal_options.generate_difference:
            response_json = response.json()
            new_features = []
            if "options" in request_dict and "avoid_polygons" in request_dict["options"]:
                request_dict.get("options").pop("avoid_polygons")
                response_no_avoid = self.relay_request_post(endpoint, request_header, request_dict)

                new_features = self.calculate_new_features(db, options, request_dict,
                                                           response_json[result_key(options)],
                                                           response_no_avoid.json()[result_key(options)])
            response_json[result_key(options)] = new_features
            response_json["bbox"] = get_overall_bbox([f.get("geometry").get("bbox") for f in new_features])

        # process result
        if options.ors_response_type.value == "gpx":
            response_body = response.text
        else:
            if not response_json:
                response_json = response.json()
            if response.status_code == 200:
                if request.portal_options.return_areas_in_response:
                    response_json["disaster_areas"] = json.loads(disaster_areas.json())
                    response_json["disaster_areas_lookup_bbox"] = lookup_bbox

                # add portal options to query
                response_json['metadata']['query']['portal_options'] = request.portal_options.dict()
            response_body = json.dumps(response_json)

        return ORSResponse(
            status_code=response.status_code,
            body=response_body,
            media_type=response.headers.get("Content-Type")
        )

    @staticmethod
    def calculate_new_features(db, options, request_dict, avoid_results, no_avoid_results):
        out_type = options.ors_response_type.value
        new_features = []
        for i, item in enumerate(no_avoid_results):
            if options.ors_api == "isochrones":
                avoid_item = ORSProcessor.get_matching_isochrone(avoid_results, item)
            else:
                avoid_item = avoid_results[i]
            # no difference
            if avoid_item == item:
                continue
            query = build_diff_query(avoid_item, item, options.ors_api, out_type)
            diff_geom = db.execute(query).scalar()
            if out_type == "json":
                avoid_item["geometry"] = diff_geom
                avoid_item["bbox"] = get_bbox_for_encoded_polyline(db, item)
            else:
                avoid_item["geometry"] = json.loads(diff_geom)
                # no difference
                if not avoid_item["geometry"]["coordinates"]:
                    continue
            ORSProcessor.update_info(avoid_item, item, options, request_dict)
            new_features.append(avoid_item)
        return new_features

    @staticmethod
    def get_matching_isochrone(avoid_results, item):
        # the number of isochrones in the avoid-response can be different from the normal one
        # thus, they are matched by the group_index and value
        for x in avoid_results:
            if has_same_prop(x, item, "group_index") and has_same_prop(x, item, "value"):
                return x
        return None

    @staticmethod
    def update_info(avoid_item, item, options, request_dict):
        if options.ors_api == "isochrones":
            for attribute in request_dict.get("attributes") or []:
                avoid_item["properties"][attribute] = item.get("properties").get(attribute) - avoid_item.get(
                    "properties").get(attribute)
        elif options.ors_api == "directions":
            item_props = item if options.ors_response_type == "json" else item["properties"]
            avoid_item_props = avoid_item if options.ors_response_type == "json" else avoid_item["properties"]
            # recalculate distance and duration
            avoid_item_props["summary"]["distance"] -= item_props["summary"]["distance"]
            avoid_item_props["summary"]["duration"] -= item_props["summary"]["duration"]
            for k, v in avoid_item_props["summary"].items():
                avoid_item_props["summary"][k] = round(v, 1)
            # drop unusable properties
            avoid_item_props.pop("way_points", None)
            avoid_item_props.pop("segments", None)

    @staticmethod
    def get_bounding_box(request: Union[ORSDirections, ORSIsochrones], target_api, target_profile) -> list:
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
    def prepare_request_dic(request: Union[ORSDirections, ORSIsochrones]) -> dict:
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


def result_key(options: PathOptions) -> str:
    """
    returns the correct key of the result list depending on the response type
    """
    return "features" if options.ors_response_type != "json" else "routes"


def has_same_prop(d1: dict, d2: dict, prop: str) -> bool:
    """
    Checks whether two features have the same value for a specific property
    """
    return d1["properties"][prop] == d2["properties"][prop]


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
