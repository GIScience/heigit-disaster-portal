"""
Objects used to parametrize tests.
These are functions as some objects are altered.
To keep the pytest output correct, pass a copy of the object to the test set instead.
"""
import json

from sqlalchemy.orm import Session

from app.schemas import PathOptions
from typing import Union
from geoalchemy2 import func


def basic_directions_geojson_item(
        dis: Union[int, float] = 5,
        dur: Union[int, float] = 5,
        geom: Union[dict, None] = None) -> dict:
    if geom is None:
        geom = {"dummy": "dummy"}
    return {
        "bbox": [0, 3, 0, 3],
        "type": "Feature",
        "properties": {
            "segments": "dummy",
            "summary": {"distance": dis, "duration": dur},
            "way_points": "dummy"},
        "geometry": geom
    }


def basic_directions_json_item(
        db: Session,
        dis: Union[int, float] = 5,
        dur: Union[int, float] = 5,
        geom: Union[dict, None] = None) -> dict:
    if geom is None:
        geom = "dummy"
    else:
        geom = db.execute(func.ST_AsEncodedPolyline(func.ST_GeomFromGeoJSON(json.dumps(geom)))).scalar()
    return {
        "bbox": [0, 3, 0, 3],
        "segments": "dummy",
        "summary": {"distance": dis, "duration": dur},
        "way_points": "dummy",
        "geometry": geom
    }


def basic_isochrones_item(
        g_id: Union[int, float] = 0,
        val: Union[int, float] = 200.0,
        geom: Union[dict, None] = None,
        a: Union[int, float] = 4,
        p: Union[int, float] = 50) -> dict:
    if geom is None:
        geom = {"dummy": "dummy"}
    return {
        "type": "Feature",
        "properties": {
            "group_index": g_id,
            "value": val,
            "center": [
                8.6814962950468,
                49.41460087012079
            ],
            "area": a,
            "total_pop": p
        },
        "geometry": geom
    }


def basic_options(api: str = "directions", res: str = "geojson") -> PathOptions:
    return PathOptions.parse_obj({
        "portal_mode": "avoid_areas",
        "ors_api": api,
        "ors_profile": "driving-car",
        "ors_response_type": res
    })


def update_info_set_1() -> tuple:
    """directions diff on distance and duration"""
    return (
        basic_directions_geojson_item(),
        basic_directions_geojson_item(dis=8, dur=15),
        basic_options(), {
            "attributes": []
        }, {
            "bbox": [0, 3, 0, 3], "type": "Feature", "properties": {
                "summary": {"distance": 3, "duration": 10}},
            "geometry": {"dummy": "dummy"}
        }
    )


def update_info_set_2() -> tuple:
    """float values are rounded"""
    return (
        basic_directions_geojson_item(dis=5.11111, dur=5.11111),
        basic_directions_geojson_item(dis=8, dur=15),
        basic_options(), {
            "attributes": []
        }, {
            "bbox": [0, 3, 0, 3], "type": "Feature", "properties": {
                "summary": {"distance": 2.9, "duration": 9.9}},
            "geometry": {"dummy": "dummy"}
        }
    )


def calc_features_set_1() -> tuple:
    d_a = basic_directions_geojson_item(dis=8, dur=15, geom={"coordinates": [[0, 0], [1, 1], [1, 2], [2, 2], [3, 3]],
                                                             "type": "LineString"})
    d = basic_directions_geojson_item(geom={"coordinates": [[0, 0], [3, 3]], "type": "LineString"})
    return (
        basic_options(res="geojson"), {
            "attributes": []
        },
        [d_a],
        [d],
        [{
            "bbox": [0, 3, 0, 3], "type": "Feature", "properties": {
                "summary": {"distance": 3, "duration": 10}},
            "geometry": {'bbox': [1.0, 1.0, 2.0, 2.0],
                         "coordinates": [[1, 1], [1, 2], [2, 2]],
                         "type": "LineString"}
        }]
    )


def calc_features_set_2() -> tuple:
    """directions no diff"""
    d = basic_directions_geojson_item()
    d['geometry'] = {"coordinates": [[0, 0], [3, 3]], "type": "LineString"}
    return (
        basic_options(res="geojson"), {
            "attributes": []
        },
        [d],
        [d],
        []
    )


def calc_features_set_3() -> tuple:
    """isochrones no diff"""
    i = basic_isochrones_item()
    return (
        basic_options(api="isochrones"),
        {
            "attributes": ["total_pop", "area"]
        },
        [i],
        [i],
        []
    )


def calc_features_set_4() -> tuple:
    """isochrones single diff"""
    i = basic_isochrones_item(geom={"coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]], "type": "Polygon"})
    i_avoid = basic_isochrones_item(geom={"coordinates": [[[0, 1], [0, 2], [2, 2], [2, 1], [0, 1]]], "type": "Polygon"},
                                    a=2, p=20)
    return (
        basic_options(api="isochrones"),
        {
            "attributes": ["total_pop", "area"]
        },
        [i_avoid],
        [i],
        [basic_isochrones_item(
            geom={"bbox": [0.0, 0.0, 2.0, 1.0], "coordinates": [[[0, 1], [2, 1], [2, 0], [0, 0], [0, 1]]],
                  "type": "Polygon"}, a=2, p=30)]
    )


def calc_features_set_5() -> tuple:
    """isochrones multi-range diff with multi polygon output"""
    i = basic_isochrones_item(
        geom={"coordinates": [[[0, 0], [2, 2], [2, 0], [0, 0]]], "type": "Polygon"})
    i_avoid = basic_isochrones_item(
        geom={"coordinates": [[[0, 0], [1, 1], [2, 0], [0, 0]]], "type": "Polygon"},
        a=2,
        p=20)
    i2 = basic_isochrones_item(
        val=400.0,
        a=10,
        p=200,
        geom={"coordinates": [[[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]], "type": "Polygon"})
    i_avoid2 = basic_isochrones_item(
        val=400.0,
        geom={"coordinates": [[[0, 1], [3, 4], [4, 4], [4, 3], [1, 0], [0, 0], [0, 1]]], "type": "Polygon"},
        a=4,
        p=120)
    return (
        basic_options(api="isochrones"),
        {
            "attributes": ["total_pop", "area"]
        },
        [i_avoid, i_avoid2],
        [i, i2],
        [
            basic_isochrones_item(
                geom={"bbox": [1.0, 0.0, 2.0, 2.0], "coordinates": [[[1, 1], [2, 2], [2, 0], [1, 1]]],
                      "type": "Polygon"}, a=2, p=30),
            basic_isochrones_item(
                val=400.0,
                a=6,
                p=80,
                geom={"bbox": [0.0, 0.0, 4.0, 4.0], "coordinates": [[[[0, 4], [3, 4], [0, 1], [0, 4]]],
                                                                    [[[4, 0], [1, 0], [4, 3], [4, 0]]]],
                      "type": "MultiPolygon"
                      }
            )
        ]
    )


def matching_iso_set_1() -> tuple:
    """isochrone match"""
    return (
        [
            basic_isochrones_item(),
            basic_isochrones_item(val=400.0),
            basic_isochrones_item(g_id=1),
            basic_isochrones_item(g_id=1, val=400.0)
        ],
        {"properties": {"group_index": 1, "value": 400.0}},
        basic_isochrones_item(g_id=1, val=400.0)
    )


def matching_iso_set_2() -> tuple:
    """no isochrone match"""
    return (
        [
            basic_isochrones_item(),
            basic_isochrones_item(val=400.0),
        ],
        {"properties": {"group_index": 1, "value": 200.0}},
        None
    )
