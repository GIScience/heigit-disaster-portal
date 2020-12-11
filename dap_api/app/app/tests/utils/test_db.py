from pydantic import PostgresDsn
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker

from app.config import settings

SQLALCHEMY_DATABASE_URL = PostgresDsn.build(
    scheme="postgresql",
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_TEST_SERVER,
    port=settings.POSTGRES_TEST_PORT,
    path=f"/{settings.POSTGRES_DB}"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
