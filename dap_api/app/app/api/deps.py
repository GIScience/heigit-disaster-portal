from app.db.session import SessionLocal


# Dependency
def get_db():  # pragma: no cover
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
