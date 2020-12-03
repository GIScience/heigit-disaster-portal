from typing import Optional, List

from pydantic import BaseModel


# Shared properties
class DisasterSubTypeBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = "Disaster area sub-type"
    parent_id: Optional[int]


# Properties to receive via API on creation
class DisasterSubTypeCreate(DisasterSubTypeBase):
    name: str
    parent_id: int


# Properties to receive via API on update
class DisasterSubTypeUpdate(DisasterSubTypeBase):
    pass


class DisasterSubTypeBaseInDBBase(DisasterSubTypeBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class DisasterSubType(DisasterSubTypeBaseInDBBase):
    pass


# Additional properties stored in DB
class DisasterSubTypeBaseInDB(DisasterSubTypeBaseInDBBase):
    pass
