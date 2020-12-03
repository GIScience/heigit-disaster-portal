from typing import Optional, List

from pydantic import BaseModel


# Shared properties
from app.schemas.disaster_sub_type import DisasterSubType


class DisasterTypeBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = "Disaster area type"


# Properties to receive via API on creation
class DisasterTypeCreate(DisasterTypeBase):
    name: str


# Properties to receive via API on update
class DisasterTypeUpdate(DisasterTypeBase):
    pass


class DisasterTypeBaseInDBBase(DisasterTypeBase):
    id: Optional[int] = None
    sub_types: Optional[List[DisasterSubType]]

    class Config:
        orm_mode = True


# Additional properties to return via API
class DisasterType(DisasterTypeBaseInDBBase):
    pass


# Additional properties stored in DB
class DisasterTypeBaseInDB(DisasterTypeBaseInDBBase):
    pass
