from fastapi import Query

from app.db.session import SessionLocal


# Dependency
def get_db():  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def common_multi_query_params(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1)
):
    return {"skip": skip, "limit": limit}
