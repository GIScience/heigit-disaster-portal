from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.api import deps

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.CollectionMetadata,
    summary="Get disaster type collection metadata"
)
def read_collection_metadata(
) -> Any:
    """
    Get disaster type collection metadata
    """
    return {
        "id": "disaster_types",
        "title": "Disaster types",
        "description": "TODO: disaster type collection info, maybe define in DB Model an call from there"
    }


@router.get(
    "/items",
    response_model=List[schemas.DisasterType],
    summary="Read Disaster Types"
)
def read_d_types(
        db: Session = Depends(deps.get_db),
        c: dict = Depends(deps.common_multi_query_params)
) -> Any:
    """
    Retrieve disaster types.
    """
    skip, limit = c.values()
    return crud.disaster_type.get_multi(db, skip=skip, limit=limit)


@router.get(
    "/items/{disaster_type}",
    response_model=schemas.DisasterType,
    summary="Read Disaster Type By Name or Id"
)
def read_d_type(
        disaster_type: int | str,
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific disaster type by id.
    """
    is_int = isinstance(disaster_type, int)
    is_str = isinstance(disaster_type, str)
    d_type = None
    if is_int:
        d_type = crud.disaster_type.get(db, id=disaster_type)
    if is_str:
        d_type = crud.disaster_type.get_by_name(db=db, name=disaster_type)
    if not d_type:
        raise HTTPException(
            status_code=404,
            detail=f"The disaster type with this {'id' if is_int else 'name' if is_str else 'term'} does not exist in "
                   f"the system",
        )
    return d_type
