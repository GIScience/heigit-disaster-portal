from typing import Any

from fastapi import APIRouter, Depends, Response, HTTPException, Header
from sqlalchemy.orm import Session

from app.api import deps
from app.backend.ors_processor import ORSProcessor
from app.config import settings
from app.schemas import ORSRequest, PathOptions

router = APIRouter()
ors_processor = ORSProcessor(settings.ORS_BACKEND_URL)


@router.get(
    "/{portal_mode}/{ors_api}/{ors_profile}",
    summary="Query ORS"
)
def ors_get(
        portal_mode: str,
        ors_api: str,
        ors_profile: str,
        api_key: str = "",
        start: str = "",
        end: str = "",
        debug: bool = False,
        db: Session = Depends(deps.get_db)
) -> Any:
    if api_key == "":
        raise HTTPException(
            status_code=400,
            detail=f"Request validation error: No api_key provided",
        )
    if start == "":
        raise HTTPException(
            status_code=400,
            detail=f"Request validation error: No start coordinates provided",
        )
    if end == "":
        raise HTTPException(
            status_code=400,
            detail=f"Request validation error: No end coordinates provided",
        )
    request = ORSRequest.parse_obj({
        "portal_options": {
          "debug": debug
        },
        "coordinates": [
            start.split(","),
            end.split(",")
        ]
    })
    return process_ors_request(portal_mode, ors_api, ors_profile, "geojson", request, api_key, db)


@router.post(
    "/{portal_mode}/{ors_api}/{ors_profile}",
    summary="Query ORS"
)
def ors_post(
        portal_mode: str,
        ors_api: str,
        ors_profile: str,
        request: ORSRequest,
        authorization: str = Header(None),
        db: Session = Depends(deps.get_db)
) -> Any:
    return process_ors_request(portal_mode, ors_api, ors_profile, "json", request, authorization, db)


@router.post(
    "/{portal_mode}/{ors_api}/{ors_profile}/{ors_response_type}",
    summary="Query ORS"
)
def ors_post_response_type(
        portal_mode: str,
        ors_api: str,
        ors_profile: str,
        ors_response_type: str,
        request: ORSRequest,
        authorization: str = Header(None),
        db: Session = Depends(deps.get_db)
) -> Any:
    return process_ors_request(portal_mode, ors_api, ors_profile, ors_response_type, request, authorization, db)


def process_ors_request(
        portal_mode: str,
        ors_api: str,
        ors_profile: str,
        ors_response_type: str,
        request: ORSRequest,
        header_authorization: str,
        db: Session
) -> Any:
    options = PathOptions(
        portal_mode=portal_mode,
        ors_api=ors_api,
        ors_profile=ors_profile,
        ors_response_type=ors_response_type
    )
    result = ors_processor.handle_ors_request(db, request, options, header_authorization)
    return Response(result.body, media_type=result.header_type)
