import json
from typing import Union

import pytest
from sqlalchemy.orm import Session

from app.backend.ors_processor import ORSProcessor, result_key, has_same_prop
from app.schemas import PathOptions
from app.schemas.ors_request import ORSIsochrones, ORSDirections
from app.tests.backend.util_test_data import update_info_set_1, update_info_set_2, calc_features_set_1, \
    calc_features_set_2, matching_iso_set_1, matching_iso_set_2, calc_features_set_3, \
    calc_features_set_4, calc_features_set_5, basic_options


class TestOrsProcessor:
    @pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
    def test_handle_ors_request(self):
        assert False

    @pytest.mark.parametrize(
        "options,request_dict,response,response_no_avoid,out", [
            calc_features_set_1(),
            calc_features_set_2(),
            calc_features_set_3(),
            calc_features_set_4(),
            calc_features_set_5()

        ]
    )
    def test_calculate_new_features(self, db: Session, options: PathOptions, request_dict, response, response_no_avoid,
                                    out):
        f = ORSProcessor.calculate_new_features(db, options, request_dict, response, response_no_avoid)
        assert f == out

    @pytest.mark.parametrize(
        "avoid_results,item,out", [
            matching_iso_set_1(),
            matching_iso_set_2()
        ]
    )
    def test_get_matching_isochrone(self, avoid_results, item, out):
        n = ORSProcessor.get_matching_isochrone(avoid_results, item)
        assert n == out

    @pytest.mark.parametrize(
        "item,avoid_item,options,request_dict,out",
        [
            update_info_set_1(),
            update_info_set_2()

        ])
    def test_update_info(self, item, avoid_item, options: PathOptions,
                         request_dict: Union[ORSDirections, ORSIsochrones], out):
        ORSProcessor.update_info(avoid_item, item, options, request_dict)
        assert json.dumps(avoid_item) == json.dumps(out)

    @pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
    def test_get_bounding_box(self):
        assert False

    @pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
    def test_prepare_request_dic(self):
        assert False

    @pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
    def test_prepare_headers(self):
        assert False


def test_result_keys():
    assert result_key(basic_options(res="json")) == "routes"
    assert result_key(basic_options()) == "features"


def test_has_same_prop():
    assert has_same_prop(
        {"properties": {"asd": True, "hello": 42}},
        {"properties": {"asd": False, "hello": 42}},
        "hello"
    ) is True
    assert has_same_prop(
        {"properties": {"asd": True, "hello": 42}},
        {"properties": {"asd": False, "hello": "42"}},
        "hello"
    ) is False
    assert has_same_prop(
        {"properties": {"asd": True, "hello": 42}},
        {"properties": {"asd": False, "hello": False}},
        "hello"
    ) is False
    assert has_same_prop(
        {"properties": {"asd": True, "hello": 42}},
        {"properties": {"asd": True, "hello": False}},
        "asd"
    ) is True
