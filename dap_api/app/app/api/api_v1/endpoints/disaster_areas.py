from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.api import deps
from app.schemas.disaster_area import DisasterAreaCollection

router = APIRouter()


@router.get(
    "/",
    response_model=DisasterAreaCollection,
    summary="Read Disaster Areas"
)
def read_disaster_areas(
        db: Session = Depends(deps.get_db),
        c: dict = Depends(deps.common_multi_query_params)
) -> Any:
    """
    Retrieve disaster areas.
    """
    skip, limit = c.values()
    return crud.disaster_area.get_multi_as_feature_collection(db, skip=skip, limit=limit)


@router.post(
    "/",
    response_model=schemas.DisasterAreaCreateOut,
    summary="Create Disaster Area"
)
def create_disaster_area(
        *,
        db: Session = Depends(deps.get_db),
        disaster_area_in: schemas.DisasterAreaCreate
) -> Any:
    """
    Create new disaster area.
    """
    provider = crud.provider.get(db, id=disaster_area_in.properties.provider_id)
    if not provider:
        raise HTTPException(
            status_code=400,
            detail="A provider with the given provider_id does not exist.",
        )
    disaster_type = crud.disaster_type.get(db, id=disaster_area_in.properties.d_type_id)
    if not disaster_type:
        raise HTTPException(
            status_code=400,
            detail="A disaster type with this id does not exists.",
        )
    disaster_area = crud.disaster_area.get_by_name(db, name=disaster_area_in.properties.name)
    if disaster_area:
        raise HTTPException(
            status_code=400,
            detail="A disaster area with this name already exists in the system.",
        )
    db_entry = crud.disaster_area.create(db, obj_in=disaster_area_in)
    return crud.disaster_area.get_as_feature(db, db_entry.id)


@router.get(
    "/items/{disaster_area_id}",
    response_model=schemas.DisasterArea,
    summary="Read Disaster Area By Id"
)
def read_disaster_area_by_id(
        disaster_area_id: int,
        db: Session = Depends(deps.get_db),
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
    summary="Update Disaster Area By Id"
)
def update_disaster_area_by_id(
        disaster_area_id: int,
        disaster_area_in: schemas.DisasterAreaUpdate,
        db: Session = Depends(deps.get_db)
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
    disaster_area = crud.disaster_area.update(db, db_obj=disaster_area, obj_in=disaster_area_in)
    return crud.disaster_area.get_as_feature(db, disaster_area.id)


@router.delete(
    "/items/{disaster_area_id}",
    response_model=schemas.DisasterArea,
    summary="Delete Disaster Area By Id",
)
def read_disaster_area_by_id(
        disaster_area_id: int,
        db: Session = Depends(deps.get_db),
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
    area_feature = crud.disaster_area.get_as_feature(db, disaster_area.id)
    crud.disaster_area.remove(db, id=disaster_area_id)
    return area_feature
