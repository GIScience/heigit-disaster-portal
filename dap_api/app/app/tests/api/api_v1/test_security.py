import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models, crud
from app.config import settings
from app.schemas import UserCreateOut
from app.tests.utils.disaster_areas import create_new_polygon, create_new_properties, create_new_disaster_area
from app.tests.utils.utils import random_email, random_lower_string


@pytest.mark.parametrize("verb", ["post", "put", "delete"])
@pytest.mark.parametrize("endpoint", ["users", "providers", "disaster_areas"])
def test_access_post_put_delete_without_auth_header(
        client: TestClient,
        verb: str,
        endpoint: str
) -> None:
    suffix = "/1" if verb != "post" else ""
    r = client.request(method=verb, url=f"{settings.API_V1_STR}/collections/{endpoint}/items{suffix}")
    r_obj = r.json()
    assert r.status_code == 401
    assert r_obj["detail"] == "Authorization header missing or invalid"


@pytest.mark.parametrize("verb", ["post", "put", "delete"])
@pytest.mark.parametrize("endpoint", ["users", "providers", "disaster_areas"])
def test_access_post_put_delete_with_invalid_auth_header(
        client: TestClient,
        verb: str,
        endpoint: str
) -> None:
    suffix = "/1" if verb != "post" else ""
    r = client.request(method=verb, url=f"{settings.API_V1_STR}/collections/{endpoint}/items{suffix}",
                       headers={"Authorization": "Bearer SomethingWrong"})
    r_obj = r.json()
    assert r.status_code == 401
    assert r_obj["detail"] == "Authorization header missing or invalid"


@pytest.mark.parametrize("verb", ["post", "put", "delete"])
@pytest.mark.parametrize("endpoint", ["users", "providers"])
def test_access_to_admin_endpoints_with_user_auth_header(
        client: TestClient,
        provider_owner_secret: str,
        verb: str,
        endpoint: str
) -> None:
    suffix = "/1" if verb != "post" else ""
    r = client.request(method=verb, url=f"{settings.API_V1_STR}/collections/{endpoint}/items{suffix}",
                       headers={"Authorization": f"Bearer {provider_owner_secret}"})
    r_obj = r.json()
    assert r.status_code == 403
    assert r_obj["detail"] == "Action only allowed for administrators"


@pytest.mark.parametrize("user,status", [
    ("owner", 200),
    ("no_owner", 403)])
def test_access_to_owner_endpoints(
        client: TestClient,
        db: Session,
        provider_owner: models.User,
        provider_owner_secret: str,
        user: str,
        status: int
) -> None:
    """
    Tests Create, Edit, Delete of disaster areas for both a user that is allowed to use the
    data provider and a user that is not the provider owner
    """
    url = f"{settings.API_V1_STR}/collections/disaster_areas/items"
    secret = provider_owner_secret
    if user == "no_owner":
        secret = "test_secret"
        user_obj = UserCreateOut(email=random_email(), secret=secret)
        crud.user.create(db, obj_in=user_obj)

    p = provider_owner.providers[0]
    d_area_props = create_new_properties(p_id=p.id)
    d_area_geom = create_new_polygon()
    data = {
        "type": "Feature",
        "properties": d_area_props.dict(),
        "geometry": d_area_geom.dict()
    }

    # POST
    r = client.post(url=url,
                    headers={"Authorization": f"Bearer {secret}"},
                    json=data)
    r_obj = r.json()
    assert r.status_code == status
    if status == 403:
        assert r_obj["detail"].startswith("You are not allowed to publish")
        d_area = create_new_disaster_area(db, p_id=p.id)
        area_id = d_area.id
    else:
        area_id = r_obj.get("id")

    # PUT
    json_edit = {**data, **{"properties": {"description": random_lower_string()}}}
    url += f"/{area_id}"

    r = client.put(url=url,
                   headers={"Authorization": f"Bearer {secret}"},
                   json=json_edit)
    r_obj = r.json()
    assert r.status_code == status
    if status == 403:
        assert r_obj["detail"].startswith("You are not allowed to edit")

    # DELETE
    r = client.delete(url=url,
                      headers={"Authorization": f"Bearer {secret}"})
    r_obj = r.json()
    assert r.status_code == status
    if status == 403:
        assert r_obj["detail"].startswith("You are not allowed to delete")
