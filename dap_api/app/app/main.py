from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/docs/openapi.json",
    docs_url=None,
    redoc_url=None
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get(f"{settings.API_V1_STR}/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico",
        with_google_fonts=False,
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
