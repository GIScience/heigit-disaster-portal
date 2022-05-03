from os.path import realpath

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

api_description = """
The HeiGIT disaster portal API manages features that can be used by applications or users
in requests to HeiGIT services.

It acts as a single entry place to the various services ([openrouteservice], [ohsome] etc.) as well as
allowing additional processing to be performed on either the requests made to these services, or the responses
returned from them.

[openrouteservice]: https://openrouteservice.org "ORS website"
[ohsome]: https://ohsome.org "ohsome website"
"""


tags = {
    "users": {
        "name": "users",
        "description": "Manage access restrictions to API functionality through users."
    },
    "providers": {
        "name": "providers",
        "description": "Disaster data providers that officially contribute data sets"
    },
    "disaster types": {
        "name": "disaster types",
        "description": "Main categories of disasters assigned to areas"
    },
    "disaster sub types": {
        "name": "disaster sub types",
        "description": "Detailed categories of disasters optionally assigned to areas"
    },
    "disaster areas": {
        "name": "disaster areas",
        "description": "Storage for disaster area geometries and their meta information"
    },
    "custom speeds": {
        "name": "custom speeds",
        "description": "Speed sets used to overwrite default speeds for `waytype` or `surface` tags"
    },
    "HeiGIT services": {
        "name": "HeiGIT services",
        "description": "Endpoints offering various different services provided by HeiGIT"
    }
}


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/docs/openapi.json",
    docs_url=None,
    redoc_url=None,
    description=api_description,
    openapi_tags=list(tags.values())
)

app.mount("/static", StaticFiles(directory=realpath(f'{realpath(__file__)}/../../static')), name="static")


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
