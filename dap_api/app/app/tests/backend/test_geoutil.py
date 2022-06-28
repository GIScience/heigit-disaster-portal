import pytest
from app.backend.geoutil import *


@pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
class TestGeoUtil:
    def test_point_from_point_bearing_distance(self):
        # point_from_point_bearing_distance()
        assert False

    def test_point_distance(self):
        # point_distance()
        assert False

    def test_bbox_length(self):
        # bbox_length()
        assert False

    @pytest.mark.parametrize("lon,out",
                             [(0, 0), (20.12, 22.12), (-999.00, 81), (999.00, -81), (-180, -180), (180, 180)])
    def test_restrict_longitude(self, lon: float, out: float):
        res = restrict_longitude(lon)
        assert res == out

    def test_restrict_latitude(self):
        # restrict_latitude()
        assert False

    def test_bbox_buffer_percentage(self):
        # bbox_buffer_percentage()
        assert False

    def test_bbox_from_radius(self):
        # bbox_from_radius()
        assert False

    def test_meters_travelled(self):
        # meters_travelled()
        assert False

    def test_build_diff_query(self):
        # build_diff_query()
        assert False

    def test_get_geom_from_item(self):
        # get_geom_from_item()
        assert False
