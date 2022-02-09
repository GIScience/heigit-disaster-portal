from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/docs/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# TODO: different api docs for different api versions.

cors_options = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
}
if settings.CORS_ORIGINS:
    cors_options["allow_origins"] = [str(origin) for origin in settings.CORS_ORIGINS]
if settings.CORS_ORIGINS_REGEX:
    cors_options["allow_origin_regex"] = settings.CORS_ORIGINS_REGEX

if settings.CORS_ORIGINS or settings.CORS_ORIGINS_REGEX:
    app.add_middleware(
        CORSMiddleware,
        **cors_options
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/")
def landing_page():
    return "TODO: static landing page"
