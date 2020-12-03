from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.schemas.provider import Provider


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr


# Properties to return via API on creation
class UserCreateOut(UserCreate):
    secret: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    secret: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    providers: Optional[List[Provider]]

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_secret: str
    is_admin: bool
