from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class ProviderBase(BaseModel):
    email: EmailStr
    name: str
    owner_id: int
    description: Optional[str] = "Disaster area provider"


# Properties to receive via API on creation
class ProviderCreate(ProviderBase):
    pass


# Properties to return via API on creation
class ProviderCreateOut(ProviderCreate):
    pass


# Properties to receive via API on update
class ProviderUpdate(ProviderBase):
    email: Optional[EmailStr]
    name: Optional[str]
    owner_id: Optional[int]
    description: Optional[str]


class ProviderInDBBase(ProviderBase):
    id: int

    class Config:
        orm_mode = True


# Additional properties to return via API
class Provider(ProviderInDBBase):
    pass


# Additional properties stored in DB
class ProviderInDB(ProviderInDBBase):
    pass
