from math import sqrt

import geopy
import geopy.distance


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
    d = geopy.distance.distance(kilometers=distance/1000)
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
