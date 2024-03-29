from typing import Any

from fastapi import APIRouter, Depends, Response, Body, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.api import deps
from app.backend.ors_processor import ORSProcessor
from app.config import settings
from app.schemas import PathOptions, OrsResponseType, PathOptionsValidation, BadRequestResponse
from app.schemas.ors_request import ORSDirections, ORSIsochrones
from app.schemas.utils import ISO_EXAMPLES, DIR_EXAMPLES, BASE_EXAMPLE

router = APIRouter()
ors_processor = ORSProcessor(settings.ORS_BACKEND_URL)


@router.get(
    "/{portal_mode}/{ors_api}/{ors_profile}",
    summary="Query ORS",
    responses={
        400: {"model": BadRequestResponse, "description": """
Bad Request       

An additional error code + message is provided.

Error `code`:
- `6404`: Custom speed set does not exist
"""
              }
    }
)
def ors_get(
        path_options: PathOptionsValidation = Depends(),
        api_key: str = Depends(deps.ors_api_key_param),
        start: str = Depends(deps.ors_start_param),
        end: str = Depends(deps.ors_end_param),
        user_speed_limits: int = None,
        debug: bool = False,
        db: Session = Depends(deps.get_db)
) -> Any:
    request = ORSDirections.parse_obj({
        "portal_options": {
            "debug": debug
        },
        "coordinates": [
            start.split(","),
            end.split(",")
        ],
        "user_speed_limits": user_speed_limits
    })
    return process_ors_request(request, api_key, db, path_options, ors_response_type=OrsResponseType("geojson"))


@router.post(
    "/{portal_mode}/{ors_api}/{ors_profile}",
    summary="Query ORS",
    responses={
        400: {"model": BadRequestResponse, "description": """
Bad Request       

An additional error code + message is provided.

Error `code`:
- `6404`: Custom Speeds does not exist
"""
              }
    }
)
def ors_post(
        request: ORSIsochrones | ORSDirections = Body(
            None,
            examples=BASE_EXAMPLE | ISO_EXAMPLES | DIR_EXAMPLES
        ),
        path_options: PathOptionsValidation = Depends(),
        authorization: str = Depends(deps.ors_auth_header),
        db: Session = Depends(deps.get_db)
) -> Any:
    response_type = OrsResponseType("geojson") if path_options.ors_api == "isochrones" else OrsResponseType("json")
    return process_ors_request(request, authorization, db, path_options, ors_response_type=response_type)


@router.post(
    "/{portal_mode}/{ors_api}/{ors_profile}/{ors_response_type}",
    summary="Query ORS",
    responses={
        400: {"model": BadRequestResponse, "description": """
Bad Request       

An additional error code + message is provided.

Error `code`:
- `6404`: Custom Speeds does not exist
"""
              }
    }
)
def ors_post_response_type(
        request: ORSIsochrones | ORSDirections = Body(
            None,
            examples=BASE_EXAMPLE | ISO_EXAMPLES | DIR_EXAMPLES
        ),
        ors_authorization: str = Depends(deps.ors_auth_header),
        db: Session = Depends(deps.get_db),
        path_options: PathOptionsValidation = Depends(),
        ors_response_type: OrsResponseType = "geojson"
) -> Any:
    return process_ors_request(request,
                               ors_authorization, db, path_options, ors_response_type)


def process_ors_request(
        request: ORSIsochrones | ORSDirections,
        header_authorization: str,
        db: Session,
        path_options: PathOptionsValidation,
        ors_response_type: OrsResponseType
) -> Any:
    path_options = PathOptions(**path_options.dict(), ors_response_type=ors_response_type)
    if path_options.ors_api == "isochrones" and isinstance(request, ORSDirections):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your request body (directions) doesn't match the ors_api ({path_options.ors_api})"
        )
    elif path_options.ors_api == "directions" and isinstance(request, ORSIsochrones):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your request body (isochrones) doesn't match the ors_api ({path_options.ors_api})"
        )
    result = ors_processor.handle_ors_request(db, request, path_options, header_authorization)
    return Response(result.body, status_code=result.status_code, media_type=result.media_type)
