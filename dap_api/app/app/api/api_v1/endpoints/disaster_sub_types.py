from typing import Any, List, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.api import deps

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.DisasterSubType],
    summary="Read Disaster Sub Types"
)
def read_ds_types(
        db: Session = Depends(deps.get_db),
        c: dict = Depends(deps.common_multi_query_params)
) -> Any:
    """
    Retrieve disaster sub types.
    """
    skip, limit = c.values()
    return crud.disaster_sub_type.get_multi(db, skip=skip, limit=limit)


@router.get(
    "/items/{disaster_sub_type}",
    response_model=schemas.DisasterSubType,
    summary="Read Disaster Sub Type By Name or Id"
)
def read_ds_type(
        disaster_sub_type: Union[int, str],
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific disaster sub type by name or id.
    """
    is_int = isinstance(disaster_sub_type, int)
    is_str = isinstance(disaster_sub_type, str)
    ds_type = None
    if is_int:
        ds_type = crud.disaster_sub_type.get(db, id=disaster_sub_type)
    if is_str:
        ds_type = crud.disaster_sub_type.get_by_name(db=db, name=disaster_sub_type)
    if not ds_type:
        raise HTTPException(
            status_code=404,
            detail=f"The disaster sub type with this {'id' if is_int else 'name' if is_str else 'term'} does not "
                   f"exist in the system",
        )
    return ds_type
