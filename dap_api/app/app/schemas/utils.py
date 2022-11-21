import json
from pathlib import Path
from typing import Any, List, Dict

from pydantic import BaseModel, Field

path = Path(__file__).parent.absolute()  # folder path of this file
with open(f'{path}/../db/init_data/d_types.json', 'r') as d_type_file:
    d_types = json.load(d_type_file)

# create lookup dict for disaster IDs from database. Result {1:[1,2],2:[3,4,5,6]...}
D_ID_LOOKUP = {d_t["id"]: [st["id"] for st in d_t["sub_types"]] for d_t in d_types}


class CollectionMetadata(BaseModel):
    id: str
    title: str
    description: str
    links: List[Dict[str, Any]] = []


class BadRequestResponse(BaseModel):
    code: int = Field(..., title="Error code", description="Internal error code providing details on the error source")
    message: str = Field(..., title="Error message", description="Error description")


class HttpErrorResponse(BaseModel):
    detail: str = Field(..., title="Error detail", description="Detailed error message")


class ErrorDetailObject(BaseModel):
    loc: List[str]
    msg: str
    type: str = "value_error"


def eg(name: str, description: str, value: dict) -> dict:
    """Generates an example object"""
    return {
        "summary": name,
        "description": description,
        "value": value
    }


BASE_EXAMPLE = {
    "All-Params": eg(
        "All parameters (please adjust)",
        "Lists all portal options. **No valid request!** Remove either `coordinates` for an `isochrones` request or"
        "`locations` and `range` for a directions request.",
        {"portal_options": {
            "debug": False,
            "return_areas_in_response": False,
            "bounds_looseness": 0,
            "generate_difference": False,
            "disaster_area_filter": {
                "bbox": [-180., -90., 180., 90.],
                "datetime": "2018-02-12T23:20:50Z/",
                "d_type_id": 1
            }
        },
            "coordinates": [[8.681495, 49.41461], [8.686507, 49.41943], [8.687872, 49.420318]],
            "locations": [[8.681495, 49.41461]],
            "range": [300, 200],
            "user_speed_limits": 1
        }
    )
}

ISO_EXAMPLES = {
    "Isochrone": eg(
        "Isochrone 5min",
        "An Isochrone with 5 minute range using avoid areas from the portal storage in this area",
        {
            "locations": [[8.681495, 49.41461]], "range": [300]
        }
    ),
    "Iso-distance": eg(
        "Iso-distance 500m",
        "An Iso-distance with 500 meter range using avoid areas from the portal storage in this area",
        {
            "locations": [[8.681495, 49.41461]], "range": [500], "range_type": "distance"
        }
    ),
    "Isochrone-multi": eg(
        "Isochrone 3min/5min",
        "An Isochrone with 1 center and 2 range using avoid areas from the portal storage in this area",
        {
            "locations": [[8.681495, 49.41461]], "range": [300, 180]
        }
    ),
    "Isochrones-multi": eg(
        "Isochrones 2 centers 3min/5min",
        "An Isochrone with 1 center and 2 range using avoid areas from the portal storage in this area",
        {
            "locations": [[8.681495, 49.41461], [8.686507, 49.41943]], "range": [300, 180]
        }
    ),
    "Isochrone-diff": eg(
        "Isochrone diff 5min",
        "Difference between the Isochrone with 5 minute range using avoid areas from the portal storage and"
        "the Isochrone with 5 minute range without avoid areas",
        {
            "portal_options": {"generate_difference": True},
            "locations": [[8.681495, 49.41461]], "range": [300]
        }
    ),
    "Isochrone-filtered": eg(
        "Isochrone 5min (filtered)",
        "Isochrone with 5 minute range using avoid areas from the portal storage filtered by a custom bbox",
        {
            "portal_options": {"disaster_area_filter": {"bbox": [8.67503, 49.40974, 8.67881, 49.41189]}},
            "locations": [[8.681495, 49.41461]], "range": [300]
        }
    )
}

DIR_EXAMPLES = {
    "Directions": eg(
        "Directions (start-end)",
        "A route with 1 start- and 1 endpoint using avoid areas from the portal storage in this area",
        {
            "coordinates": [[8.681495, 49.41461], [8.687872, 49.420318]]
        }
    ),
    "Directions via": eg(
        "Directions (start-via-end)",
        "A route with 1 start-, 1 via and 1 endpoint using avoid areas from the portal storage in this area",
        {
            "coordinates": [[8.681495, 49.41461], [8.686507, 49.41943], [8.687872, 49.420318]]
        }
    ),
    "Directions-diff": eg(
        "Directions diff (start-end)",
        "A route with 1 start- and 1 endpoint using avoid areas from the portal storage in this area",
        {
            "portal_options": {"generate_difference": True},
            "coordinates": [[8.681495, 49.41461], [8.687872, 49.420318]]
        }
    ),
    "Directions-filtered": eg(
        "Directions (filtered)",
        "A route with 1 start- and 1 endpoint using avoid areas from the portal storage filtered by disaster type",
        {
            "portal_options": {"disaster_area_filter": {"d_type_id": 12}},
            "coordinates": [[8.681495, 49.41461], [8.687872, 49.420318]]
        }
    ),
    "Directions-speed-limits": eg(
        "Directions (speed limits)",
        "A route using customized road speeds. May also be used together with `portal_mode=avoid_areas`.",
        {
            "coordinates": [[8.681495, 49.41461], [8.687872, 49.420318]],
            "user_speed_limits": {
                "roadSpeeds": {
                    "road": 10
                },
                "unit": "kmh"
            }
        }
    ),
    "Directions-speed-limits-id": eg(
        "Directions (speed limits by ID)",
        "Using the `custom_speeds_id` from an object in the `custom_speeds` collection to resolve the"
        " `user_speed_limits` object. May also be used together with `portal_mode=avoid_areas`.",
        {
            "coordinates": [[8.681495, 49.41461], [8.687872, 49.420318]],
            "user_speed_limits": 1
        }
    ),
}

bbox_parameter = {
    "default": ["-180., -90., 180., 90"],
    "title": "Bbox",
    "description": """
Bounding box to request features in, as comma separated float values west(lon), south(lat), east(lon), north(lat).

Can also be passed in this order in separate query parameter instances like
`?bbox=west&bbox=south&bbox=east&bbox=north`.

**Contrary to the specified bbox array type, float values need to be passed instead of a string!**
"""
}

datetime_parameter = {
    "default": "2018-02-12T23:20:50Z/",
    "title": "datetime",
    "alias": "datetime",
    "description": """
Either a date-time or an interval, open or closed. Date and time expressions
adhere to RFC 3339. Open intervals are expressed using double-dots or an empty string (unknown start/stop).
Timestamps with timezones (`+01:00` instead of Z) as well as fractions (2018-02-12T23:20:50.25Z) are supported.

Examples:

* A date-time: `2018-02-12T23:20:50Z`
* A closed interval: `2018-02-12T00:00:00Z/2018-03-18T12:31:12Z`
* Open intervals: `2018-02-12T00:00:00Z/..` or `/2018-03-18T12:31:12Z`

Only features that have a temporal property that intersects the value of
`datetime` are selected.
In addition, all features without a temporal geometry are selected.
"""
}
