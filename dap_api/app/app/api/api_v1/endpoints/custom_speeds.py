from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette import status
from app import schemas, crud, models
from app.api import deps

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.CollectionMetadata,
    summary="Get custom speeds collection metadata"
)
def read_collection_metadata(
) -> Any:
    """
    Get custom speeds collection metadata
    """
    return {
        "id": "custom_speeds",
        "title": "Custom speeds",
        "description": "TODO: custom speeds collection info, maybe define in DB Model an call from there"
    }


@router.get(
    "/items",
    response_model=List[schemas.CustomSpeedsOut],
    summary="Read Custom Speeds"
)
def read_custom_speeds(
        db: Session = Depends(deps.get_db),
        c: dict = Depends(deps.common_multi_query_params)
) -> Any:
    """
    Retrieve disaster areas.
    """
    skip, limit = c.values()
    res = crud.custom_speeds.get_multi(db, skip=skip, limit=limit)
    return res


@router.post(
    "/items",
    response_model=schemas.CustomSpeedsOut,
    summary="Create custom speeds entry",
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
def create_custom_speeds(
        *,
        db: Session = Depends(deps.get_db),
        custom_speeds_in: schemas.CustomSpeedsCreate,
        user: models.User = Depends(deps.check_auth_header)
) -> Any:
    """
    Create new custom speeds entry
    """
    provider = crud.provider.get(db, id=custom_speeds_in.properties.provider_id)
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
    custom_speeds = crud.custom_speeds.get_by_name(db, name=custom_speeds_in.properties.name)
    if custom_speeds:
        return JSONResponse(status_code=400, content={
            "code": 5409,
            "message": "A disaster area with this name already exists in the system."
        })
    db_entry = crud.custom_speeds.create(db, obj_in=custom_speeds_in)
    return crud.custom_speeds.get(db, db_entry.id)


@router.get(
    "/items/{custom_speeds_id}",
    response_model=schemas.CustomSpeedsOut,
    summary="Read Custom Speeds By Id",
    responses={
        404: {"model": schemas.HttpErrorResponse, "description": "Item not found"}
    }
)
def read_custom_speeds_by_id(
        custom_speeds_id: int,
        db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get a specific disaster area by id.
    """
    custom_speeds = crud.custom_speeds.get(db, cs_id=custom_speeds_id)
    if not custom_speeds:
        raise HTTPException(
            status_code=404,
            detail="The custom_speeds with this id does not exist in the system",
        )
    return custom_speeds


@router.put(
    "/items/{custom_speeds_id}",
    response_model=schemas.CustomSpeedsOut,
    summary="Update Custom Speeds By Id",
    responses={
        404: {"model": schemas.HttpErrorResponse, "description": "Item not found"}
    }
)
def update_custom_speeds_by_id(
        custom_speeds_id: int,
        custom_speeds_in: schemas.CustomSpeedsUpdate,
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.check_auth_header)
) -> Any:
    """
    Update a specific custom speeds entry by id.
    """
    custom_speeds = crud.custom_speeds.get(db, cs_id=custom_speeds_id)
    if not custom_speeds:
        raise HTTPException(
            status_code=404,
            detail="Custom speeds not found",
        )
    provider = crud.provider.get(db, id=custom_speeds.properties.provider_id)
    if not (user.is_admin or user.id == provider.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to edit data for this provider. "
                   f"Please contact them at {provider.email}",
        )
    custom_speeds = crud.custom_speeds.update(db, cs_id=custom_speeds_id, obj_in=custom_speeds_in)
    return crud.custom_speeds.get(db, custom_speeds.id)


@router.delete(
    "/items/{custom_speeds_id}",
    response_model=schemas.CustomSpeedsOut,
    summary="Delete Disaster Area By Id",
    responses={
        404: {"model": schemas.HttpErrorResponse, "description": "Item not found"}
    }
)
def delete_custom_speeds_by_id(
        custom_speeds_id: int,
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.check_auth_header)
) -> Any:
    """
    Delete a specific disaster area by id.
    """
    cs = crud.custom_speeds.get(db, cs_id=custom_speeds_id)
    if not cs:
        raise HTTPException(
            status_code=404,
            detail="Custom speeds with this id does not exist in the system",
        )
    provider = crud.provider.get(db, id=cs.properties.provider_id)
    if not (user.is_admin or user.id == provider.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete data for this provider. "
                   f"Please contact them at {provider.email}",
        )
    crud.custom_speeds.remove(db, id=custom_speeds_id)
    return cs
