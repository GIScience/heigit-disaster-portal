from typing import Any, List, Dict

from pydantic import BaseModel, Field


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
            "generate_difference": False
        },
            "coordinates": [[8.681495, 49.41461], [8.686507, 49.41943], [8.687872, 49.420318]],
            "locations": [[8.681495, 49.41461]],
            "range": [300, 200]
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
}
