from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps
from app.security import generate_secret

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.CollectionMetadata,
    summary="Get user collection metadata"
)
def read_collection_metadata(
) -> Any:
    """
    Get user collection metadata
    """
    return {
        "id": "users",
        "title": "Users",
        "description": "TODO: user collection info, maybe define in DB Model an call from there"
    }


@router.get(
    "/items",
    response_model=List[schemas.User],
    summary="Read Users"
)
def read_users(
        db: Session = Depends(deps.get_db),
        c: dict = Depends(deps.common_multi_query_params)
) -> Any:
    """
    Retrieve users.
    """
    skip, limit = c.values()
    return crud.user.get_multi(db, skip=skip, limit=limit)


@router.post(
    "/items",
    response_model=schemas.UserCreateOut,
    summary="Create User"
)
def create_user(
        *,
        db: Session = Depends(deps.get_db),
        admin: models.User = Depends(deps.check_admin_auth),
        user_in: schemas.UserCreate
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists in the system.",
        )
    user_with_secret = schemas.UserCreateIn(**user_in.dict(), secret=generate_secret())
    user_out_db = crud.user.create(db, obj_in=user_with_secret)
    # if settings.EMAILS_ENABLED and user_in.email:
    #     send_new_account_email(
    #         email_to=user_in.email, username=user_in.email, password=user_in.password
    #     )
    return schemas.UserCreateOut(**user_with_secret.dict(), id=user_out_db.id)


@router.get(
    "/items/{user_id}",
    response_model=schemas.User,
    summary="Read User By Id"
)
def read_user_by_id(
        user_id: int,
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    return user


@router.put(
    "/items/{user_id}",
    response_model=schemas.User,
    summary="Update User By Id"
)
def update_user_by_id(
        user_id: int,
        user_in: schemas.UserUpdate,
        db: Session = Depends(deps.get_db),
        admin: models.User = Depends(deps.check_admin_auth)
) -> Any:
    """
    Update a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete(
    "/items/{user_id}",
    response_model=schemas.User,
    summary="Delete User By Id",
)
def delete_user_by_id(
        user_id: int,
        db: Session = Depends(deps.get_db),
        admin: models.User = Depends(deps.check_admin_auth)
) -> Any:
    """
    Delete a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = crud.user.remove(db, id=user_id)
    return user
