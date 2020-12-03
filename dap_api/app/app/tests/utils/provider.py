from sqlalchemy.orm import Session

from app import crud
from app.schemas import ProviderCreateOut, Provider, User
from app.tests.utils.utils import random_email, random_lower_string


def create_new_provider(
        db: Session,
        provider_owner: User
) -> Provider:
    p_obj = ProviderCreateOut(
        email=random_email(), name=random_lower_string(8), owner_id=provider_owner.id
    )
    return crud.provider.create(
        db=db,
        obj_in=p_obj
    )
