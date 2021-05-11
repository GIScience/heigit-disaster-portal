"""
Reusable dependencies that are injected into different endpoints
"""
from typing import List, Optional

from dateutil.parser import isoparse
from fastapi import Query, HTTPException, Header, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette import status

from app import crud, models
from app.db.session import SessionLocal
from app.schemas.disaster_area import BBoxModel

from app.schemas.utils import ErrorDetailObject
from app.security import auth_header


def get_db():  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_valid_bbox(bbox: Optional[List[str]] = Query(
    ["-180., -90., 180., 90"],
    title="Bbox",
    description="""
Bounding box to request features in, as comma separated float values west(lon), south(lat), east(lon), north(lat).

Can also be passed in this order in separate query parameter instances like
`?bbox=west&bbox=south&bbox=east&bbox=north`.

**Contrary to the specified bbox array type, float values need to be passed instead of a string!**
"""
)
):
    if len(bbox) != 4:
        bbox = [float(x) for x in bbox[0].split(',')]
    try:
        bbox_obj = BBoxModel.parse_obj(bbox)
    except ValidationError as e:
        for error in e.errors():
            error['loc'] = ["query", "bbox"]
        raise HTTPException(
            status_code=422,
            detail=e.errors()
        )
    return bbox_obj


def common_multi_query_params(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1)
):
    return {"skip": skip, "limit": limit}


def ors_api_key_param(api_key: str = Query(None)):
    if not api_key:
        raise HTTPException(status_code=400, detail="Openrouteservice api key missing in api_key parameter")
    return api_key


def ors_start_param(start: str = Query(None)):
    if not start:
        raise HTTPException(status_code=400, detail="Start coordinates parameter missing")
    coordinates = start.split(",")
    if len(coordinates) != 2:
        raise HTTPException(status_code=400, detail="Start coordinates parameter invalid")
    for c in coordinates:
        try:
            float(c)
        except ValueError:
            raise HTTPException(status_code=400, detail="Start coordinates parameter invalid")
    return start


def ors_end_param(end: str = Query(None)):
    if not end:
        raise HTTPException(status_code=400, detail="End coordinates parameter missing")
    coordinates = end.split(",")
    if len(coordinates) != 2:
        raise HTTPException(status_code=400, detail="End coordinates parameter invalid")
    for c in coordinates:
        try:
            float(c)
        except ValueError:
            raise HTTPException(status_code=400, detail="End coordinates parameter invalid")
    return end


def ors_auth_header(ors_authorization: str = Header(None)):
    if not ors_authorization:
        raise HTTPException(status_code=400, detail="Openrouteservice api key missing in authorization header")
    return ors_authorization


def check_auth_header(db: Session = Depends(get_db),
                      authorization: HTTPAuthorizationCredentials = Depends(auth_header)) -> models.User:
    http_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authorization header missing or invalid",
    )
    # authorization header is not passed
    if authorization is None:
        raise http_exception
    user = crud.user.get_by_secret(db=db, secret=authorization.credentials)
    # secret is not found
    if user is None:
        raise http_exception
    return user


def check_admin_auth(user: models.User = Depends(check_auth_header)) -> models.User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action only allowed for administrators"
        )
    return user


def date_time_or_interval(date_time: str = Query(
    "2018-02-12T23:20:50Z/",
    title="datetime",
    alias="datetime",
    description="""Either a date-time or an interval, open or closed. Date and time expressions
adhere to RFC 3339. Open intervals are expressed using double-dots or an empty string (unknown start/stop).
Timestamps with timezones (`+01:00` instead of Z) as well as fractions (2018-02-12T23:20:50.25Z) are supported.

Examples:

* A date-time: `2018-02-12T23:20:50Z`
* A closed interval: `2018-02-12T00:00:00Z/2018-03-18T12:31:12Z`
* Open intervals: `2018-02-12T00:00:00Z/..` or `/2018-03-18T12:31:12Z`

Only features that have a temporal property that intersects the value of
`datetime` are selected.
In addition, all features without a temporal geometry are selected. 
"""
)) -> Optional[str]:
    if date_time is None:
        return
    errors = []
    date_time_array = date_time.split('/')
    if len(date_time_array) == 1:
        try:
            isoparse(date_time)
        except ValueError as e:
            errors.append(ErrorDetailObject(
                loc=["query", "datetime"],
                msg=f"Invalid timestamp {date_time}: {e}"
            ).dict())
    elif len(date_time_array) == 2:
        date1, date2 = date_time_array
        if date1 not in ['', '..']:
            try:
                isoparse(date1)
            except ValueError as e:
                errors.append(ErrorDetailObject(
                    loc=["query", "datetime"],
                    msg=f"Invalid start timestamp {date_time}: {e}"
                ).dict())
        if date2 not in ['', '..']:
            try:
                isoparse(date2)
            except ValueError as e:
                errors.append(ErrorDetailObject(
                    loc=["query", "datetime"],
                    msg=f"Invalid stop timestamp {date_time}: {e}"
                ).dict())
    if not errors == []:
        raise HTTPException(
            status_code=422,
            detail=errors
        )
    return date_time
