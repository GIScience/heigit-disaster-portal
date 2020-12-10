from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.api import deps

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Provider],
    summary="Read Providers"
)
def read_providers(
        db: Session = Depends(deps.get_db),
        c: dict = Depends(deps.common_multi_query_params)
) -> Any:
    """
    Retrieve providers.
    """
    skip, limit = c.values()
    return crud.provider.get_multi(db, skip=skip, limit=limit)


@router.post(
    "/",
    response_model=schemas.ProviderCreateOut,
    summary="Create Provider"
)
def create_provider(
        *,
        db: Session = Depends(deps.get_db),
        provider_in: schemas.ProviderCreate
) -> Any:
    """
    Create new provider.
    """
    owner = crud.user.get(db, id=provider_in.owner_id)
    if not owner:
        raise HTTPException(
            status_code=400,
            detail="A User with the provided owner_id does not exist.",
        )
    provider = crud.provider.get_by_email(db, email=provider_in.email)
    if provider:
        raise HTTPException(
            status_code=400,
            detail="A provider with this email already exists in the system.",
        )
    provider = crud.provider.get_by_name(db, name=provider_in.name)
    if provider:
        raise HTTPException(
            status_code=400,
            detail="A provider with this name already exists in the system.",
        )
    provider_out = schemas.ProviderCreateOut(**provider_in.dict())
    crud.provider.create(db, obj_in=provider_out)
    return provider_out


@router.get(
    "/items/{provider_id}",
    response_model=schemas.Provider,
    summary="Read Provider By Id"
)
def read_provider_by_id(
        provider_id: int,
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific provider by id.
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="The provider with this id does not exist in the system",
        )
    return provider


@router.put(
    "/items/{provider_id}",
    response_model=schemas.Provider,
    summary="Update Provider By Id"
)
def update_provider_by_id(
        provider_id: int,
        provider_in: schemas.ProviderUpdate,
        db: Session = Depends(deps.get_db)
) -> Any:
    """
    Update a specific provider by id.
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider not found",
        )
    provider = crud.provider.update(db, db_obj=provider, obj_in=provider_in)
    return provider


@router.delete(
    "/items/{provider_id}",
    response_model=schemas.Provider,
    summary="Delete Provider By Id",
)
def read_provider_by_id(
        provider_id: int,
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Delete a specific provider by id.
    """
    provider = crud.provider.get(db, id=provider_id)
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="The provider with this id does not exist in the system",
        )
    provider = crud.provider.remove(db, id=provider_id)
    return provider
