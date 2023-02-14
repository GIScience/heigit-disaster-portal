import json

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.backend.ors_processor import ORSProcessor, result_key, has_same_prop
from app.config import settings
from app.schemas import PathOptions
from app.schemas.ors_request import ORSIsochrones, ORSDirections
from app.tests.backend.util_test_data import update_info_set_1, update_info_set_2, calc_features_set_1, \
    calc_features_set_2, matching_iso_set_1, matching_iso_set_2, calc_features_set_3, \
    calc_features_set_4, calc_features_set_5, basic_options


class TestOrsProcessor:
    @pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
    @pytest.mark.parametrize(
        "request_dict,options,header_authorization,out", [
            (ORSDirections.parse_obj({
                "coordinates": [
                    [
                        8.681495,
                        49.41461
                    ],
                    [
                        8.687872,
                        49.420318
                    ]
                ]
            }), PathOptions.parse_obj({
                "portal_mode": "avoid_areas",
                "ors_api": "directions",
                "ors_profile": "driving-car",
                "ors_response_type": "geojson"
            }), "mock_api_key", "")
        ]
    )
    def test_handle_ors_request(self, mocker: MockerFixture, db: Session, request_dict: ORSDirections | ORSIsochrones, options: PathOptions,
                                header_authorization: str, out):
        mock_requests = mocker.patch('app.backend.base.requests')
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Type": "application/geo+json;charset=UTF-8"
        }
        mock_response.json.return_value = {
            'metadata': {
                'query': {

                }
            }
        }
        mock_requests.post.return_value = mock_response
        ors_p = ORSProcessor(settings.ORS_BACKEND_URL)
        res = ors_p.handle_ors_request(db, request_dict, options, header_authorization)
        # mock_requests
        assert out == res

    def test_handle_ors_request_with_ors_server(self, mocker: MockerFixture, db: Session):
        mock_requests = mocker.patch('app.backend.base.requests')
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Type": "application/geo+json;charset=UTF-8"
        }
        mock_response.json.return_value = {
            'metadata': {
                'query': {

                }
            }
        }
        mock_requests.post.return_value = mock_response
        ors_p = ORSProcessor(settings.ORS_BACKEND_URL)
        ors_p.handle_ors_request(db, request=ORSDirections.parse_obj({
                "portal_options": {"ors_server": "disaster1"},
                "coordinates": [
                    [
                        8.681495,
                        49.41461
                    ],
                    [
                        8.687872,
                        49.420318
                    ]
                ]
            }), options=PathOptions.parse_obj({
                "portal_mode": "avoid_areas",
                "ors_api": "directions",
                "ors_profile": "driving-car",
                "ors_response_type": "geojson"
            }), header_authorization="mock_api_key")

        assert mock_requests.method_calls[0][2]['url'].startswith('disaster1')


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
                         request_dict: ORSDirections | ORSIsochrones, out):
        ORSProcessor.update_info(avoid_item, item, options, request_dict)
        assert json.dumps(avoid_item) == json.dumps(out)

    @pytest.mark.parametrize(
        "coords,out", [
            ([[0, 0], [1, 1]], [0, 0, 1, 1]),
            ([[0, 0], [1, 1], [-2, 3]], [-2, 0, 1, 3])
        ])
    def test_get_bounding_box_directions(self, coords, out):
        result = ORSProcessor.get_bounding_box(
            request=ORSDirections(coordinates=coords),
            target_api='directions',
            target_profile='driving-car'
        )
        assert result == out

    @pytest.mark.parametrize(
        "ranges,loc,profile,diffs", [
            ([60], [[0.1, 0.1]], 'driving-car', [0.01, 0.02]),
            ([60], [[0.01, 0.01]], 'cycling-regular', [0.002, 0.004]),
            ([60], [[0.001, 0.001], [2.1, 3.32]], 'foot-walking', [0.0007, 0.0008]),
            ([120], [[0.1, 0.1]], 'driving-car', [0.02, 0.03]),
            ([60, 120, 240], [[0.1, 0.1], [1, 1]], 'driving-car', [0.04, 0.05]),
        ])
    def test_get_bounding_box_isochrones(self, ranges, loc, profile, diffs):
        result = ORSProcessor.get_bounding_box(
            request=ORSIsochrones(
                range=ranges,
                locations=loc
            ),
            target_api='isochrones',
            target_profile=profile
        )
        # bottom left difference
        diff_x = abs(loc[0][0] - result[0])
        diff_y = abs(loc[0][1] - result[1])
        # top right difference. respects 1 or 2 locations
        diff_x_top = abs(loc[len(loc) - 1][0] - result[2])
        diff_y_top = abs(loc[len(loc) - 1][1] - result[3])

        assert diffs[0] < diff_x < diffs[1]
        assert diffs[0] < diff_y < diffs[1]
        assert diffs[0] < diff_x_top < diffs[1]
        assert diffs[0] < diff_y_top < diffs[1]

    def test_get_bounding_box_custom(self):
        """
        Should return the bbox specified in disaster_area_filters if present
        """
        bbox = [0, 0, 1, 1]
        request = ORSDirections.parse_obj({
            "coordinates": [[0, 0], [0, 0]],
            "portal_options": {
                "disaster_area_filter": {
                    "bbox": bbox
                }
            }
        })
        result = ORSProcessor.get_bounding_box(request, 'directions', 'driving-car')
        assert result == bbox

    @pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
    def test_prepare_request_dic(self):
        # ORSProcessor.prepare_request_dic()
        assert False

    @pytest.mark.skipif(True, reason="TODO")  # TODO: WIP
    def test_prepare_headers(self):
        # ORSProcessor.prepare_headers()
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
