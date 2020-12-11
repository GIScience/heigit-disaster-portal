import logging
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app import crud
from app.api.deps import get_db
from app.config import settings
from app.db.base import BaseTable
from app.db.init_db import init_db
from app.main import app
from app.schemas import UserCreateOut
from app.security import generate_secret
from app.tests.utils.overrides import override_get_db
from app.tests.utils.test_db import engine, TestSession
from app.tests.utils.utils import random_email

app.dependency_overrides[get_db] = override_get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """

    """
    BaseTable.metadata.drop_all(bind=engine)
    BaseTable.metadata.create_all(bind=engine)
    print()
    logger.info(f"Creating initial db data on server {settings.POSTGRES_TEST_SERVER}:{settings.POSTGRES_TEST_PORT}")
    db = TestSession()
    init_db(db=db)
    logger.info("Initial db data created")
    yield  # Run the tests.


@pytest.fixture(scope="session")
def db() -> Generator:

    yield TestSession()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def provider_owner(db: TestSession):
    username = random_email()
    user_obj = UserCreateOut(email=username, secret=generate_secret())
    return crud.user.create(db, obj_in=user_obj)

#
#
# @pytest.fixture(scope="module")
# def superuser_token_headers(client: TestClient) -> Dict[str, str]:
#     return get_superuser_token_headers(client)
#
#
# @pytest.fixture(scope="module")
# def normal_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
#     return authentication_token_from_email(
#         client=client, email=settings.EMAIL_TEST_USER, db=db
#     )
