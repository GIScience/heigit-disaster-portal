import json
from typing import List

import geopy
import geopy.distance
from geoalchemy2 import func
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import Function

from app.schemas import OrsApi, OrsResponseType


def point_from_point_bearing_distance(lon: float, lat: float, bearing: float, distance: float) -> (float, float):
    """
    create point from source point, bearing and distance
    @param lon: longitude
    @param lat: latitude
    @param bearing: in degree
    @param distance: in meters
    @return: (lon, lat) point
    """
    lon_prc = lat_prc = 7
    if bearing in [0, 180]:
        lon_prc = float_precision(lon)
    if bearing in [90, 270]:
        lat_prc = float_precision(lat)
    start = geopy.Point(lat, lon)
    d = geopy.distance.distance(kilometers=distance / 1000)
    goal = d.destination(point=start, bearing=bearing)
    return round(goal.longitude, lon_prc), round(goal.latitude, lat_prc)


def point_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    return distance in meters between two geographic points
    @param lon1: point 1 longitude
    @param lat1: point 1 latitude
    @param lon2: point 2 longitude
    @param lat2: point 2 latitude
    @return: distance between point 1 and 2 in meters
    """
    return geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).meters


def bbox_length(bbox: List[float]) -> float:
    """
     return max of bbox width / length, not used now but potentially in future versions to improve
     calculations in bbox_buffer_percentage
    """
    return max(point_distance(bbox[0], bbox[1], bbox[2], bbox[1]), point_distance(bbox[0], bbox[1], bbox[0], bbox[3]))


def restrict_longitude(lon: float) -> float | int:
    """
    Restricts longitude to valid range of -180 to 180
    @param lon: longitude
    @return: valid longitude
    """
    if -180 <= lon <= 180:
        return int(lon) if float(lon).is_integer() else lon
    elif lon > 180:
        return restrict_longitude(lon - 360)
    elif lon < -180:
        return restrict_longitude(lon + 360)


def restrict_latitude(lat: float) -> float | int:
    """
    Restricts latitude to valid range of -90 to 90
    @param lat: latitude
    @return: valid latitude
    """
    if lat > 90:
        return 90
    if lat < -90:
        return -90
    return int(lat) if float(lat).is_integer() else lat


def buffer_bbox(bbox: List[float | int], p: float = 0, d: float = 0) -> List[float | int]:
    """
    buffer bbox length and width by percentage and/or distance in terms of coordinate units.
    Bboxes are generally expecting WGS84 (EPSG: 4326) coordinates.
    @param bbox: bbox to buffer
    @param p: buffer percentage
    @param d: buffer distance
    @return: buffered bbox
    """
    lon_dist = (bbox[2] - bbox[0]) * p / 100
    lat_dist = (bbox[3] - bbox[1]) * p / 100
    return [
        restrict_longitude(round(bbox[0] - (lon_dist + d), 6)),
        restrict_latitude(round(bbox[1] - (lat_dist + d), 6)),
        restrict_longitude(round(bbox[2] + (lon_dist + d), 6)),
        restrict_latitude(round(bbox[3] + (lat_dist + d), 6))
    ]


def bbox_from_radius(lon: float, lat: float, radius: float) -> List[float | int]:
    """
    calculate bbox for a circle around a point with radius
    @param lon: center longitude
    @param lat: center latitude
    @param radius: of the circle in meters for which the bbox should be calculated
    @return: calculated bbox
    """
    lon1, _ = point_from_point_bearing_distance(lon, lat, 270, radius)
    _, lat1 = point_from_point_bearing_distance(lon, lat, 180, radius)
    lon2, _ = point_from_point_bearing_distance(lon, lat, 90, radius)
    _, lat2 = point_from_point_bearing_distance(lon, lat, 0, radius)
    return [
        restrict_longitude(min(lon1, lon2)),
        restrict_latitude(min(lat1, lat2)),
        restrict_longitude(max(lon1, lon2)),
        restrict_latitude(max(lat1, lat2))
    ]


def meters_travelled(seconds: float, speed: float) -> int:
    """
    return meters travelled in x seconds for a specific speed in kmh
    @param seconds: travel time in seconds
    @param speed: travel speed in km/h
    @return: travel distance in meters
    """
    return round(seconds * speed / 3600 * 1000)


def build_diff_query(avoid_item: dict, item: dict, ors_api: OrsApi, ors_res_type: OrsResponseType) -> Function:
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


def get_bbox_for_encoded_polyline(db: Session, item: dict) -> float | int:
    """
    Returns the bbox for the encoded polyline of a json route item
    @param db: db session
    @param item: route item in json format
    @return: bbox for the encoded polyline route
    """
    geom = get_geom_from_item(item, OrsResponseType.json)
    bbox_geojson = db.execute(func.ST_AsGeoJson(func.Box2D(geom), 5, 1)).scalar()
    return json.loads(bbox_geojson)["bbox"]


def get_geom_from_item(item: dict, ors_res_type: OrsResponseType) -> Function:
    """
    Extract the geometry from the correct place in the response item
    depending on the response format
    @param item: single route or isochrone item
    @param ors_res_type: response format
    @return: geoalchemy function for PostGIS geometry of the ors response
    """
    geom = item.get('geometry')
    if ors_res_type == 'geojson':
        geom = func.ST_GeomFromGeoJSON(json.dumps(geom))
    elif ors_res_type == 'json':
        geom = func.ST_LineFromEncodedPolyline(geom)
    return geom


def get_overall_bbox(bboxes: List[List[float]]) -> List[float]:
    """
    Returns bbox for multiple bboxes (2D or 3D)
    @param bboxes: list of bboxes
    @return: bbox containing every bbox of the passed list
    """
    tuples = [x for x in list(zip(*bboxes))]
    bbox = []
    for i, t in enumerate(tuples):
        bbox.append(min(t) if i < len(tuples) / 2 else max(t))
    return bbox


def float_precision(f: float, limit: int = 7) -> int:
    """
    Returns the precision of a float or the precision limit.
    Can be used for rounding operations.
    @param f: input float
    @param limit: maximum float precision
    @return: precision of input float
    """
    digits = 0
    if not float(f).is_integer():
        digits = len(str(f).split(".")[1])
    return digits if digits <= limit else limit
