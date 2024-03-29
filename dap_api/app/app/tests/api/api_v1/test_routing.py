import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import DisasterAreaPropertiesCreate, Polygon
from app.tests.utils.custom_speeds import create_new_custom_speeds


# ---------------------------------- For debugging purposes ----------------------------------

def create_disaster_areas_for_testing(
    db: Session
):
    # create disaster areas in database for testing: one does intersect with the request's bbox and should be added,
    # the other does not intersect and should not turn up.
    crud.disaster_area.create(db, obj_in=DisasterAreaCreate(
        geometry=Polygon(
            coordinates=[[[0.0001, 0.0002], [0.0003, 0.0004], [0.0006, 0.0005], [0.0001, 0.0002]]]
        ),
        properties=DisasterAreaPropertiesCreate(
            name="not intersecting",
            d_type_id=1,
            provider_id=1,
            description="This polygon is outside of the request bbox"
        )
    ))
    crud.disaster_area.create(db, obj_in=DisasterAreaCreate(
        geometry=Polygon(
            coordinates=[
                [
                    [
                        8.683,
                        49.4212
                    ],
                    [
                        8.6871,
                        49.4214
                    ],
                    [
                        8.6871,
                        49.4182
                    ],
                    [
                        8.682,
                        49.4181
                    ],
                    [
                        8.683,
                        49.4212
                    ]
                ]
            ]
        ),
        properties=DisasterAreaPropertiesCreate(
            name="intersecting",
            d_type_id=1,
            provider_id=1,
            description="This polygon should be in the request bbox"
        )
    ))


def test_routing_api_post(
    db: Session,
    client: TestClient
) -> None:
    create_disaster_areas_for_testing(db)
    data = {
        "coordinates": [
            [
                8.678613,
                49.411721
            ],
            [
                8.714733,
                49.393267
            ],
            [
                8.687782,
                49.424597
            ]
        ],
        "preference": "recommended",
        "instructions": False,
        "portal_options": {
            # In debug mode, the modified request gets returned instead of relayed to ORS backend.
            # To actually relay the request to a locally running ORS instance with default test graph data, set
            # debug to False. If the instance is running a graph built from the default OSM test data provided with
            # ORS (heidelberg.osm.gz), the query should return a valid route. This is also required to test
            # functionality of the 'return_areas_in_response' parameter.
            # Alternatively, you can unset ORS_BACKEND_URL in .env-dev, in which case ors_processor attempts to connect
            # to ORS at https://api.openrouteservice.org/v2. You have to provide an API key below for this to work.
            "debug": True,
            "return_areas_in_response": True,
            "bounds_looseness": 50
        },
        "options": {
            "avoid_borders": "controlled",

            # The following two blocks can be uncommented to test behavior in case an avoid_polygon option is already
            # present in the original request.

            # type Polygon
            # "avoid_polygons": {
            #     "coordinates": [
            #         [
            #             [
            #                 8.68,
            #                 49.421
            #             ],
            #             [
            #                 8.687,
            #                 49.421
            #             ],
            #             [
            #                 8.687,
            #                 49.418
            #             ],
            #             [
            #                 8.68,
            #                 49.418
            #             ],
            #             [
            #                 8.68,
            #                 49.421
            #             ]
            #         ]
            #     ],
            #     "type": "Polygon"
            # }

            # type MultiPolygon
            # "avoid_polygons": {
            #     "coordinates": [
            #         [
            #             [
            #                 [
            #                     8.68,
            #                     49.421
            #                 ],
            #                 [
            #                     8.687,
            #                     49.421
            #                 ],
            #                 [
            #                     8.687,
            #                     49.418
            #                 ],
            #                 [
            #                     8.68,
            #                     49.418
            #                 ],
            #                 [
            #                     8.68,
            #                     49.421
            #                 ]
            #             ]
            #         ]
            #     ],
            #     "type": "MultiPolygon"
            # }

        },
    }
    api_key = "An API key"
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car/json", json=data, headers={"ORS-Authorization": api_key}
    )
    r_obj = r.json()
    # Uncomment to display response
    # print(f"\n\n{json.dumps(r_obj, indent=4)}")
    assert 200 <= r.status_code < 300
    assert len(r_obj["options"]["avoid_polygons"]["coordinates"]) == 1


def test_routing_api_get(
        client: TestClient
) -> None:
    """
    !! Uses same avoid area as test_routing_api_post !!
    @param client:
    """
    r = client.get(f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car?api_key=some%20key&start=8.678613,49.411721&end=8.687782,49.424597&debug=1")
    r_obj = r.json()
    # Uncomment to display response
    # print(f"\n\n{json.dumps(r_obj, indent=4)}")
    assert 200 <= r.status_code < 300
    assert len(r_obj["options"]["avoid_polygons"]["coordinates"]) == 1


# ---------------------------------- custom speeds ----------------------------------


def test_routing_api_cs_get(
        client: TestClient, db: Session
) -> None:
    cs = create_new_custom_speeds(db)
    r = client.get(f"{settings.API_V1_STR}/routing/custom_speeds/directions/driving-car?api_key=some%20key&start=8.678613,49.411721&end=8.687782,49.424597&debug=1&user_speed_limits={cs.id}")
    r_obj = r.json()
    assert 200 <= r.status_code < 300
    assert r_obj["user_speed_limits"]["surfaceSpeeds"]["gravel"] == 75


def test_routing_api_cs_get_nonexistent(
        client: TestClient
) -> None:
    r = client.get(f"{settings.API_V1_STR}/routing/custom_speeds/directions/driving-car?api_key=some%20key&start=8.678613,49.411721&end=8.687782,49.424597&debug=1&user_speed_limits=123456")
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["code"] == 6404
    assert r_obj["message"] == "A Custom speeds entry with the given ID does not exist."


def test_routing_api_cs_post(
        db: Session,
        client: TestClient
) -> None:
    cs = create_new_custom_speeds(db)
    data = {
        "coordinates": [
            [
                8.678613,
                49.411721
            ],
            [
                8.687782,
                49.424597
            ]
        ],
        "preference": "recommended",
        "instructions": False,
        "portal_options": {
            "debug": True,
        },
        "user_speed_limits": cs.id
    }
    api_key = "An API key"
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car/json", json=data, headers={"ORS-Authorization": api_key}
    )
    r_obj = r.json()
    assert 200 <= r.status_code < 300
    assert r_obj["user_speed_limits"]["surfaceSpeeds"]["gravel"] == 75


def test_routing_api_cs_post_nonexistent(
        db: Session,
        client: TestClient
) -> None:
    cs = create_new_custom_speeds(db)
    data = {
        "coordinates": [
            [
                8.678613,
                49.411721
            ],
            [
                8.687782,
                49.424597
            ]
        ],
        "preference": "recommended",
        "instructions": False,
        "portal_options": {
            "debug": True,
        },
        "user_speed_limits": 123456
    }
    api_key = "An API key"
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car/json", json=data, headers={"ORS-Authorization": api_key}
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["code"] == 6404
    assert r_obj["message"] == "A Custom speeds entry with the given ID does not exist."


def test_routing_api_cs_post_combined(
        db: Session,
        client: TestClient
) -> None:
    cs = create_new_custom_speeds(db)
    data = {
        "coordinates": [
            [
                8.678613,
                49.411721
            ],
            [
                8.714733,
                49.393267
            ],
            [
                8.687782,
                49.424597
            ]
        ],
        "preference": "recommended",
        "instructions": False,
        "portal_options": {
            "debug": True,
        },
        "options": {
            "avoid_borders": "controlled",
        },
        "user_speed_limits": cs.id
    }
    api_key = "An API key"
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car/json", json=data, headers={"ORS-Authorization": api_key}
    )
    r_obj = r.json()
    assert 200 <= r.status_code < 300
    assert r_obj["user_speed_limits"]["surfaceSpeeds"]["gravel"] == 75
    assert len(r_obj["options"]["avoid_polygons"]["coordinates"]) == 1

# ---------------------------------- isochrones ----------------------------------


def test_isochrones_api_post(
    client: TestClient
) -> None:
    data = {
        "locations": [
            [
                8.678613,
                49.411721
            ]
        ],
        "range": [
            300,
            200
        ],
        "portal_options": {
            "debug": True,
            "return_areas_in_response": True,
        },
    }
    api_key = "An API key"
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/isochrones/driving-car", json=data, headers={"ORS-Authorization": api_key}
    )
    result = json.dumps(r.json(), indent=4)
    # Uncomment to display response
    # print(f"\n\n{result}")
    assert 200 <= r.status_code < 300
    assert len(result) > 0


# ---------------------------------- HTTP GET validation ----------------------------------

INVALID_ENUM_VALUE_MESSAGE = "value is not a valid enumeration member; permitted: "


def test_routing_api_missing_key_get(
    client: TestClient
) -> None:
    r = client.get(f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car?start=8.678613,49.411721&end=8.687782,49.424597")
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["detail"] == "Openrouteservice api key missing in api_key parameter"


def test_routing_api_missing_start(
    client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car?api_key=some%20key&end=8.687782,49.424597")
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["detail"] == "Start coordinates parameter missing"


def test_routing_api_missing_end(
    client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car?api_key=some%20key&start=8.678613,49.411721")
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["detail"] == "End coordinates parameter missing"


def test_routing_api_invalid_start(
    client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car?api_key=some%20key&start=8.678613&end=8.687782,49.424597")
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["detail"] == "Start coordinates parameter invalid"


def test_routing_api_invalid_end(
    client: TestClient
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car?api_key=some%20key&start=8.678613,49.411721&end=8.687782,1.1.1.1")
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["detail"] == "End coordinates parameter invalid"

# ---------------------------------- HTTP POST validation ----------------------------------


def test_routing_api_missing_key_post(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/unknown/directions/driving-car/json", json={}
    )
    r_obj = r.json()
    assert r.status_code == 400
    assert r_obj["detail"] == "Openrouteservice api key missing in authorization header"


def test_routing_api_invalid_mode(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/unknown/directions/driving-car/json", json={}, headers={"ORS-Authorization": "xxx"}
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["path", "portal_mode"]
    assert str(r_obj["detail"][0]["msg"]).startswith(INVALID_ENUM_VALUE_MESSAGE)
    assert str(r_obj["detail"][0]["msg"]).endswith("'avoid_areas', 'custom_speeds'")


def test_routing_api_invalid_api(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/unknown/driving-car/json", json={}, headers={"ORS-Authorization": "yyy"}
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["path", "ors_api"]
    assert str(r_obj["detail"][0]["msg"]).startswith(INVALID_ENUM_VALUE_MESSAGE)


def test_routing_api_invalid_profile(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/unknown/json", json={}, headers={"ORS-Authorization": "zzz"}
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["path", "ors_profile"]
    assert str(r_obj["detail"][0]["msg"]).startswith(INVALID_ENUM_VALUE_MESSAGE)

def test_routing_api_invalid_response_type(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car/unknown", json={}, headers={"ORS-Authorization": "API key"}
    )
    r_obj = r.json()
    assert r.status_code == 422
    assert r_obj["detail"][0]["loc"] == ["path", "ors_response_type"]
    assert str(r_obj["detail"][0]["msg"]).startswith(INVALID_ENUM_VALUE_MESSAGE)
