from typing import Any, List, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.api import deps
from app.security import generate_secret

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.DisasterType],
    summary="Read Disaster Types"
)
def read_users(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100
) -> Any:
    """
    Retrieve disaster types.
    """
    d_types = crud.disaster_type.get_multi(db, skip=skip, limit=limit)
    return d_types


@router.get(
    "/items/{disaster_type}",
    response_model=schemas.DisasterType,
    summary="Read Disaster Type By Name or Id"
)
def read_d_type(
        disaster_type: Union[int, str],
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
