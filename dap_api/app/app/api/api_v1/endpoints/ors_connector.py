from typing import Any

from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.backend.ors_processor import ORSProcessor
from app.config import settings
from app.schemas import ORSRequest, PathOptions, OrsResponseType, PathOptionsValidation

router = APIRouter()
ors_processor = ORSProcessor(settings.ORS_BACKEND_URL)


@router.get(
    "/{portal_mode}/{ors_api}/{ors_profile}",
    summary="Query ORS"
)
def ors_get(
        path_options: PathOptionsValidation = Depends(),
        api_key: str = Depends(deps.ors_api_key_param),
        start: str = "",
        end: str = "",
        debug: bool = False,
        db: Session = Depends(deps.get_db)
) -> Any:
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
    return process_ors_request(request, api_key, db, path_options, ors_response_type=OrsResponseType("geojson"))


@router.post(
    "/{portal_mode}/{ors_api}/{ors_profile}",
    summary="Query ORS"
)
def ors_post(
        request: ORSRequest,
        path_options: PathOptionsValidation = Depends(),
        authorization: str = Depends(deps.ors_auth_header),
        db: Session = Depends(deps.get_db)
) -> Any:
    return process_ors_request(request, authorization, db, path_options, ors_response_type=OrsResponseType("json"))


@router.post(
    "/{portal_mode}/{ors_api}/{ors_profile}/{ors_response_type}",
    summary="Query ORS"
)
def ors_post_response_type(
        request: ORSRequest,
        ors_authorization: str = Depends(deps.ors_auth_header),
        db: Session = Depends(deps.get_db),
        path_options: PathOptionsValidation = Depends(),
        ors_response_type: OrsResponseType = "geojson"
) -> Any:
    return process_ors_request(request,
                               ors_authorization, db, path_options, ors_response_type)


def process_ors_request(
        request: ORSRequest,
        header_authorization: str,
        db: Session,
        path_options: PathOptionsValidation,
        ors_response_type: OrsResponseType
) -> Any:
    path_options = PathOptions(**path_options.dict(), ors_response_type=ors_response_type)
    result = ors_processor.handle_ors_request(db, request, path_options, header_authorization)
    return Response(result.body, media_type=result.header_type)
