import json

from fastapi.testclient import TestClient
from geojson_pydantic.geometries import Polygon
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.schemas import DisasterAreaCreate
from app.schemas.disaster_area import DisasterAreaPropertiesCreate
from app.tests.utils.utils import random_lower_string


# For debugging purposes
def test_routing_api(
    db: Session,
    client: TestClient
) -> None:
    # create disaster areas in database for testing: one does intersect with the request's bbox and should be added,
    # the other does not intersect and should not turn up.
    crud.disaster_area.create(db, obj_in=DisasterAreaCreate(
        geometry=Polygon(
            coordinates=[[[0.0001, 0.0002], [0.0003, 0.0004], [0.0006, 0.0005], [0.0001, 0.0002]]]
        ),
        properties=DisasterAreaPropertiesCreate(
            name=f"",
            d_type_id=1,
            provider_id=1
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
            name=f"{random_lower_string(8)}",
            d_type_id=1,
            provider_id=1
        )
    ))

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
            "return_areas_in_response": True
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
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car/json", json=data, headers={"Authorization": api_key}
    )
    result = json.dumps(r.json(), indent=4)
    # Uncomment to display response
    # print()
    # print(result)
    assert 200 <= r.status_code < 300
    assert len(result) > 0


def test_routing_api_get(
    client: TestClient
) -> None:
    r = client.get(f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car?api_key=some%20key&start=8.678613,49.411721&end=8.687782,49.424597&debug=1")
    result = json.dumps(r.json(), indent=4)
    # Uncomment to display response
    # print()
    # print(result)
    assert 200 <= r.status_code < 300
    assert len(result) > 0


def test_routing_api_invalid_mode(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/unknown/directions/driving-car/json", json={},
    )
    assert 400 == r.status_code
    assert r.text == '{"detail":"Request validation error: Portal mode \'unknown\' not supported"}'


def test_routing_api_invalid_api(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/unknown/driving-car/json", json={},
    )
    assert 400 == r.status_code
    assert r.text == '{"detail":"Request validation error: ORS API \'unknown\' not supported"}'


def test_routing_api_invalid_profile(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/unknown/json", json={},
    )
    assert 400 == r.status_code
    assert r.text == '{"detail":"Request validation error: ORS profile \'unknown\' not supported"}'


def test_routing_api_invalid_response_type(
        client: TestClient
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/routing/avoid_areas/directions/driving-car/unknown", json={},
    )
    assert 400 == r.status_code
    assert r.text == '{"detail":"Request validation error: ORS response type \'unknown\' not supported"}'
