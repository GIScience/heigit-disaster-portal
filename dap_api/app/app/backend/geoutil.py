import json
from math import sqrt
from typing import List

import geopy
import geopy.distance
from geoalchemy2 import func
from sqlalchemy.sql.functions import Function


def point_from_point_bearing_distance(lon, lat, bearing, distance):
    """
    create point from source point, bearing and distance
    @param lon:
    @param lat:
    @param distance:
    @param bearing:
    @return:
    """
    start = geopy.Point(lat, lon)
    d = geopy.distance.distance(kilometers=distance / 1000)
    goal = d.destination(point=start, bearing=bearing)
    return goal.longitude, goal.latitude


def point_distance(lon1, lat1, lon2, lat2):
    """
    return distance in meters between two geographic points
    @param lon1:
    @param lat1:
    @param lon2:
    @param lat2:
    @return:
    """
    return geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).meters


def bbox_length(bbox):
    """
     return max of bbox width / length, not used now but potentially in future versions to improve
     calculations in bbox_buffer_percentage
    """
    return max(point_distance(bbox[0], bbox[1], bbox[2], bbox[1]), point_distance(bbox[0], bbox[1], bbox[0], bbox[3]))


def restrict_longitude(lon):
    """
    Restricts longitude to valid range of -180 to 180
    @param lon: longitude
    @return: valid lon
    """
    if lon > 180:
        return lon - 360
    if lon < -180:
        return lon + 360
    return lon


def restrict_latitude(lat):
    """
    Restricts latitude to valid range of -90 to 90
    @param lat: latitude
    @return: valid lat
    """
    if lat > 90:
        return 90
    if lat < -90:
        return -90
    return lat


def bbox_buffer_percentage(bbox, buffer):
    """
    add buffer percentage to width/length of bbox
    this is a very rough estimation, need to replace with correct geodesic calculations for production version
    @param bbox:
    @param buffer:
    @return:
    """
    looseness_factor = buffer / 200
    leeway = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) * looseness_factor
    return [
        restrict_longitude(round(bbox[0] - leeway, 6)),
        restrict_latitude(round(bbox[1] - leeway, 6)),
        restrict_longitude(round(bbox[2] + leeway, 6)),
        restrict_latitude(round(bbox[3] + leeway, 6))
    ]


def bbox_from_radius(lon, lat, radius):
    """
    calculate bbox for a circle around a point with radius
    @param lon:
    @param lat:
    @param radius:
    @return:
    """
    corner_distance = round(sqrt(2 * pow(radius, 2)))
    lon1, lat1 = point_from_point_bearing_distance(lon, lat, 315, corner_distance)
    lon2, lat2 = point_from_point_bearing_distance(lon, lat, 135, corner_distance)
    return [
        restrict_longitude(min(lon1, lon2)),
        restrict_latitude(min(lat1, lat2)),
        restrict_longitude(max(lon1, lon2)),
        restrict_latitude(max(lat1, lat2))
    ]


def meters_travelled(seconds, speed):
    """
    return meters travelled in x seconds for a specific speed in kmh
    @param seconds:
    @param speed:
    @return:
    """
    return round(seconds * speed / 3600 * 1000)


def build_diff_query(avoid_item, item, ors_api, ors_res_type) -> Function:
    """
    build the sql query to calculate the geometric difference between
    corresponding isochrone or route items.
    The returned query can be executed using a db session.
    @param avoid_item: item of the ors response with avoid areas
    @param item: item of the ors response without avoid areas
    @param ors_api: ors service
    @param ors_res_type: response format
    @return: sqlalchemy query function
    """
    geom_no_avoid = get_geom_from_item(item, ors_res_type)
    geom = get_geom_from_item(avoid_item, ors_res_type)
    difference = None
    # the difference needs to be calculated with the larger/longer geometry as base geometry (first argument)
    if ors_api == "isochrones":
        difference = func.ST_Difference(geom_no_avoid, geom)
    elif ors_api == "directions":
        difference = func.ST_Difference(geom, geom_no_avoid)
    m_valid = func.ST_MakeValid(difference)
    query = func.ST_AsGeoJson(m_valid, 7, 1)
    if ors_res_type == 'json':
        query = func.ST_AsEncodedPolyline(m_valid)
    return query


def get_bbox_for_encoded_polyline(db, item):
    """
    Returns the bbox for the encoded polyline of a json route item
    @param db: db session
    @param item: route item in json format
    @return: bbox for the encoded polyline route
    """
    geom = get_geom_from_item(item, "json")
    bbox_geojson = db.execute(func.ST_AsGeoJson(func.Box2D(geom), 5, 1)).scalar()
    return json.loads(bbox_geojson)["bbox"]


def get_geom_from_item(item: dict, ors_res_type):
    """
    Extract the geometry from the correct place in the response item
    depending on the response format
    @param item: single route or isochrone item
    @param ors_res_type: response format
    @return: item of the ors response
    """
    geom = item.get('geometry')
    if ors_res_type == 'geojson':
        geom = func.ST_GeomFromGeoJSON(json.dumps(geom))
    elif ors_res_type == 'json':
        geom = func.ST_LineFromEncodedPolyline(geom)
    return geom


def get_overall_bbox(bboxes: List[List[float]]) -> List[float]:
    """
    Returns bbox for multiple bboxes
    @param bboxes: list of bboxes
    @return:
    """
    tuples = [x for x in list(zip(*bboxes))]
    bbox = []
    for i, t in enumerate(tuples):
        bbox.append(min(t) if i < len(tuples) / 2 else max(t))
    return bbox
