from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette import status

from app import schemas, crud, models
from app.api import deps

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.CollectionMetadata,
    summary="Get disaster area collection metadata"
)
def read_collection_metadata(
) -> Any:
    """
    Get disaster area collection metadata
    """
    return {
        "id": "disaster_areas",
        "title": "Disaster areas",
        "description": "TODO: disaster area collection info, maybe define in DB Model an call from there"
    }


@router.get(
    "/items",
    response_model=schemas.DisasterAreaCollection,
    summary="Read Disaster Areas",
    responses={
        400: {"model": schemas.BadRequestResponse, "description": """
Bad Request

An additional error code + message is provided.

Error `code`:
- `3404`: Disaster type does not exist
"""
              }
    }
)
def read_disaster_areas(
        db: Session = Depends(deps.get_db),
        bbox: Optional[list] = Depends(deps.get_valid_bbox),
        date_time: str = Depends(deps.date_time_or_interval),
        d_type_id: Optional[int] = Query(None, gt=0),
        c: dict = Depends(deps.common_multi_query_params)
) -> Any:
    """
    Retrieve disaster areas.
    """
    skip, limit = c.values()
    if d_type_id is not None:
        disaster_type = crud.disaster_type.get(db, id=d_type_id)
        if not disaster_type:
            return JSONResponse(status_code=400, content={
                "code": 3404,
                "message": "A disaster type with this id does not exists."
            })
    return crud.disaster_area.get_multi_as_feature_collection(
        db, skip=skip, limit=limit, bbox=bbox, d_type_id=d_type_id, date_time=date_time
    )


@router.post(
    "/items",
    response_model=schemas.DisasterAreaCreateOut,
    summary="Create Disaster Area",
    responses={
        400: {"model": schemas.BadRequestResponse, "description": """
Bad Request

An additional error code + message is provided.

Error `code`:
- `2404`: Provider does not exist
- `3404`: Disaster type does not exist
- `5409`: Disaster area name already in use
"""
              }
    }
)
def create_disaster_area(
        *,
        db: Session = Depends(deps.get_db),
        disaster_area_in: schemas.DisasterAreaCreate,
        user: models.User = Depends(deps.check_auth_header)
) -> Any:
    """
    Create new disaster area.
    """
    provider = crud.provider.get(db, id=disaster_area_in.properties.provider_id)
    if not provider:
        return JSONResponse(status_code=400, content={
            "code": 2404,
            "message": "A provider with the given provider_id does not exist."
        })
    if not (user.is_admin or user.id == provider.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to publish data for this provider. "
                   f"Please contact them at {provider.email}",
        )
    disaster_type = crud.disaster_type.get(db, id=disaster_area_in.properties.d_type_id)
    if not disaster_type:
        return JSONResponse(status_code=400, content={
            "code": 3404,
            "message": "A disaster type with this id does not exists."
        })
    disaster_area = crud.disaster_area.get_by_name(db, name=disaster_area_in.properties.name)
    if disaster_area:
        return JSONResponse(status_code=400, content={
            "code": 5409,
            "message": "A disaster area with this name already exists in the system."
        })
    db_entry = crud.disaster_area.create(db, obj_in=disaster_area_in)
    return crud.disaster_area.get_as_feature(db, db_entry.id)


@router.get(
    "/items/{disaster_area_id}",
    response_model=schemas.DisasterArea,
    summary="Read Disaster Area By Id",
    responses={
        404: {"model": schemas.HttpErrorResponse, "description": "Item not found"}
    }
)
def read_disaster_area_by_id(
        disaster_area_id: int,
        db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get a specific disaster area by id.
    """
    disaster_area = crud.disaster_area.get(db, id=disaster_area_id)
    if not disaster_area:
        raise HTTPException(
            status_code=404,
            detail="The disaster_area with this id does not exist in the system",
        )
    return crud.disaster_area.get_as_feature(db, id=disaster_area_id)


@router.put(
    "/items/{disaster_area_id}",
    response_model=schemas.DisasterArea,
    summary="Update Disaster Area By Id",
    responses={
        404: {"model": schemas.HttpErrorResponse, "description": "Item not found"}
    }
)
def update_disaster_area_by_id(
        disaster_area_id: int,
        disaster_area_in: schemas.DisasterAreaUpdate,
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.check_auth_header)
) -> Any:
    """
    Update a specific disaster area by id.
    """
    disaster_area = crud.disaster_area.get(db, id=disaster_area_id)
    if not disaster_area:
        raise HTTPException(
            status_code=404,
            detail="Disaster area not found",
        )
    provider = crud.provider.get(db, id=disaster_area.provider_id)
    if not (user.is_admin or user.id == provider.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to edit data for this provider. "
                   f"Please contact them at {provider.email}",
        )
    disaster_area = crud.disaster_area.update(db, db_obj=disaster_area, obj_in=disaster_area_in)
    return crud.disaster_area.get_as_feature(db, disaster_area.id)


@router.delete(
    "/items/{disaster_area_id}",
    response_model=schemas.DisasterArea,
    summary="Delete Disaster Area By Id",
    responses={
        404: {"model": schemas.HttpErrorResponse, "description": "Item not found"}
    }
)
def delete_disaster_area_by_id(
        disaster_area_id: int,
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.check_auth_header)
) -> Any:
    """
    Delete a specific disaster area by id.
    """
    disaster_area = crud.disaster_area.get(db, id=disaster_area_id)
    if not disaster_area:
        raise HTTPException(
            status_code=404,
            detail="The disaster_area with this id does not exist in the system",
        )
    provider = crud.provider.get(db, id=disaster_area.provider_id)
    if not (user.is_admin or user.id == provider.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete data for this provider. "
                   f"Please contact them at {provider.email}",
        )
    area_feature = crud.disaster_area.get_as_feature(db, disaster_area.id)
    crud.disaster_area.remove(db, id=disaster_area_id)
    return area_feature
