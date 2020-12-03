from .test_db import TestSession


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()
