from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_timeout=60,
    pool_size=20,
    max_overflow=50  #
    # connect_args={"check_same_thread": False}  # only needed for SQLite DB
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
