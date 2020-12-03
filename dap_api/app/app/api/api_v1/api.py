
from fastapi import APIRouter

from app.api.api_v1.endpoints import users, providers, disaster_types

api_router = APIRouter()
api_router.include_router(users.router, prefix="/collections/users", tags=["users"])
api_router.include_router(providers.router, prefix="/collections/providers", tags=["providers"])
api_router.include_router(disaster_types.router, prefix="/collections/disaster_types", tags=["disaster types"])

