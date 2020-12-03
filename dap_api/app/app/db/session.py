from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI
    # connect_args={"check_same_thread": False}  # only needed for SQLite DB
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
