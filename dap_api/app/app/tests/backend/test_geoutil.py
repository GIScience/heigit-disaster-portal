import pytest
from app.backend.geoutil import *
from app.tests.backend.util_test_data import basic_directions_json_item, basic_directions_geojson_item, \
    basic_isochrones_item


def _get_clauses(f: Function, level: int = 0):
    if level == 0:
        return f.clauses.clauses
    else:
        return _get_clauses(f.clauses.clauses[0], level - 1)


class TestGeoUtil:
    @pytest.mark.parametrize(
        "lon,lat,bearing,distance,out",
        [(0, 0, 0, 10000, (0.0, 0.0904369)),
         (8.681495, 49.41461, 90, 1, (8.6815088, 49.41461)),
         (8.681495, 49.41461, 180, 10, (8.681495, 49.4145201)),
         (8.681495, 49.41461, 270, 10, (8.6813572, 49.41461)),
         (8.681495, 49.41461, 30, 10, (8.6815639, 49.4146879))
         ])
    def test_point_from_point_bearing_distance(self, lon, lat, bearing, distance, out):
        p = point_from_point_bearing_distance(lon, lat, bearing, distance)
        assert p == out

    @pytest.mark.parametrize(
        "lon1,lat1,lon2,lat2,out",
        [(0, 0, 0, 0, 0),
         (8.681495, 49.41461, 8.68148, 49.4145, 12.28),
         (-179.999, 0, 179.999, 0, 222.64)])
    def test_point_distance(self, lon1, lat1, lon2, lat2, out):
        distance = point_distance(lon1, lat1, lon2, lat2)
        assert round(distance, 2) == out

    @pytest.mark.parametrize(
        "bbox,out",
        [([0, 0, 0.001, 0.002], 221.15), ([8.681495, 49.41461, 8.68148, 49.4145], 12.23)])
    def test_bbox_length(self, bbox, out):
        length = bbox_length(bbox)
        assert round(length, 2) == out

    @pytest.mark.parametrize("lon,out",
                             [(0, 0), (20.12, 20.12), (-999.0, 81), (999.0, -81), (-180, -180), (180, 180)])
    def test_restrict_longitude(self, lon: float, out: float):
        res = restrict_longitude(lon)
        assert res == out

    @pytest.mark.parametrize("lat,out",
                             [(0, 0), (20.12, 20.12), (-99.00, -90.), (999.00, 90), (-90, -90), (90, 90)])
    def test_restrict_latitude(self, lat, out):
        res = restrict_latitude(lat)
        assert res == out

    @pytest.mark.parametrize(
        "bbox,p,d,out",
        [
            ([0, 0, 10, 20], 10, 0, [-1, -2, 11, 22]),
            ([0, 0, 10, 20], 0, 10, [-10, -10, 20, 30]),
            ([0, 0, 10, 20], 10, 10, [-11, -12, 21, 32]),
            ([-179, -89, 179, 89], 0, 10, [171.0, -90, -171.0, 90])
        ]
    )
    def test_buffer_bbox(self, bbox, p, d, out):
        new_bbox = buffer_bbox(bbox, p, d)
        assert new_bbox == out

    @pytest.mark.parametrize(
        "lon,lat,r,out",
        [
            (0, 0, 200000, [-1.7966306, -1.8087329, 1.7966306, 1.8087329]),
            (2, 2, 200000, [0.2022824, 0.1912692, 3.7977176, 3.8086908]),
            (8.681495, 49.41461, 20, [8.6812194, 49.4144302, 8.6817706, 49.4147898])
        ])
    def test_bbox_from_radius(self, lon, lat, r, out):
        bbox = bbox_from_radius(lon, lat, r)
        assert bbox == out

    @pytest.mark.parametrize(
        "seconds,speed,out",
        [(0, 100, 0),
         (1000, 0, 0),
         (60, 36, 600),
         (3600, 1, 1000),
         ])
    def test_meters_travelled(self, seconds, speed, out):
        meters = meters_travelled(seconds, speed)
        assert meters == out

    @pytest.mark.parametrize(
        "avoid_item,item,ors_api,ors_res_type",
        [
            (basic_directions_geojson_item(geom={"type": "LineString",
                                                 "coordinates": [[0.1, 3.6], [0.2, 2.1], [0.4, 4.1], [0.6, 5.1],
                                                                 [0.4, 5.2]]}),
             basic_directions_geojson_item(
                 geom={"type": "LineString", "coordinates": [[0.1, 3.6], [0.2, 2.1], [0.4, 5.2]]}),
             OrsApi.directions, OrsResponseType.geojson),
            (basic_isochrones_item(geom={"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}),
             basic_isochrones_item(geom={"type": "Polygon", "coordinates": [[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]]}),
             OrsApi.isochrones, OrsResponseType.geojson)
        ])
    def test_build_diff_query_geojson(self, db: Session, avoid_item, item, ors_api, ors_res_type):
        query = build_diff_query(avoid_item, item, ors_api, ors_res_type)
        assert query.description == "ST_AsGeoJSON"
        assert _get_clauses(query)[0].description == "ST_MakeValid"
        assert _get_clauses(query, 1)[0].description == "ST_Difference"
        first_diff_function_value = json.loads(_get_clauses(query, 3)[0].value)
        if ors_api == 'directions':
            assert first_diff_function_value == avoid_item.get("geometry")
        elif ors_api == 'isochrones':
            assert first_diff_function_value == item.get("geometry")

    @pytest.mark.parametrize(
        "avoid_item,item,ors_api,ors_res_type",
        [
            ({"type": "LineString", "coordinates": [[0.1, 3.6], [0.2, 2.1], [0.4, 4.1], [0.6, 5.1], [0.4, 5.2]]},
             {"type": "LineString", "coordinates": [[0.1, 3.6], [0.2, 2.1], [0.4, 5.2]]},
             OrsApi.directions, OrsResponseType.json)
        ])
    def test_build_diff_query_json(self, db: Session, avoid_item, item, ors_api, ors_res_type):
        avoid_item = basic_directions_json_item(db, geom=avoid_item)
        item = basic_directions_json_item(db, geom=item)
        query = build_diff_query(avoid_item, item, ors_api, ors_res_type)
        assert query.description == "ST_AsEncodedPolyline"
        assert _get_clauses(query)[0].description == "ST_MakeValid"
        assert _get_clauses(query, 1)[0].description == "ST_Difference"
        assert _get_clauses(query, 3)[0].value == avoid_item.get("geometry")

    @pytest.mark.parametrize(
        "geom,out",
        [
            ({"type": "LineString", "coordinates": [[0.1, 3.602], [0.22, 2.11], [0.42, 4.123], [0.3102, 5.12312]]},
             [0.1, 2.11, 0.42, 5.12312]),
            ({"type": "LineString", "coordinates": [[0, 0], [1, 1], [0, 2]]},
             [0, 0, 1, 2]),
            ({"type": "LineString", "coordinates": [[0.11111111, 3.00000900], [22.88888888, 2.11]]},
             [0.11111, 2.11, 22.88889, 3.00001])  # encoded polylines are only stored with 5 digit precision
        ])
    def test_get_bbox_for_encoded_polyline(self, db: Session, geom, out):
        item = basic_directions_json_item(db, geom=geom)
        bbox = get_bbox_for_encoded_polyline(db, item)
        assert bbox == out

    @pytest.mark.parametrize(
        "item,ors_res_type,out",
        [
            ({"type": "LineString", "coordinates": [[0.1, 0.1], [0.22, 0.1]]},
             OrsResponseType.json,
             "ST_LineFromEncodedPolyline"),
            (basic_directions_geojson_item(
                geom={"type": "LineString", "coordinates": [[0.1, 0.1], [0.22, 0.1]]}),
             OrsResponseType.geojson,
             "ST_GeomFromGeoJSON"),
            (basic_isochrones_item(
                geom={"type": "Polygon", "coordinates": [[[0.1, 0.1], [0.22, 0.1], [0.22, 0.123], [0.1, 0.1]]]}),
             OrsResponseType.geojson,
             "ST_GeomFromGeoJSON")
            # encoded polylines are only stored with 5 digit precision
        ])
    def test_get_geom_from_item(self, db: Session, item, ors_res_type, out):
        item = item if ors_res_type == "geojson" else basic_directions_json_item(db, geom=item)
        query = get_geom_from_item(item, ors_res_type)
        assert query.description == out

    @pytest.mark.parametrize(
        "bboxes,out",
        [([[0.1, 2.11, 0.42, 5.123123]], [0.1, 2.11, 0.42, 5.123123]),
         ([[0, 0, 10.1, 5.0], [-4.1, 3.8951, 0.1, 3.9]], [-4.1, 0, 10.1, 5.0])
         ])
    def test_get_overall_bbox(self, bboxes, out):
        box = get_overall_bbox(bboxes)
        assert box == out

    @pytest.mark.parametrize(
        "f,limit,out",
        [(0, None, 0),
         (1.1, None, 1),
         (1.000000001, 9, 9),
         (1.000000001, None, 7)
         ])
    def test_float_precision(self, f, limit, out):
        p = float_precision(f, limit) if limit else float_precision(f)
        assert p == out
