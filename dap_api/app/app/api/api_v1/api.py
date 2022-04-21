from fastapi import APIRouter

from app.api.api_v1.endpoints import users, providers, disaster_types, disaster_sub_types, disaster_areas, custom_speeds, ors_connector

api_router = APIRouter()
api_router.include_router(users.router, prefix="/collections/users", tags=["users"])
api_router.include_router(providers.router, prefix="/collections/providers", tags=["providers"])
api_router.include_router(disaster_types.router, prefix="/collections/disaster_types", tags=["disaster types"])
api_router.include_router(disaster_sub_types.router, prefix="/collections/disaster_sub_types", tags=["disaster sub "
                                                                                                     "types"])
api_router.include_router(disaster_areas.router, prefix="/collections/disaster_areas", tags=["disaster areas"])
api_router.include_router(custom_speeds.router, prefix="/collections/custom_speeds", tags=["custom speeds"])

api_router.include_router(ors_connector.router, prefix="/routing", tags=["HeiGIT services"])
