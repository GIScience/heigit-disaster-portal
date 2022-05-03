import secrets

from fastapi.security import HTTPBearer

from passlib.hash import bcrypt_sha256

from app.config import settings


def generate_hash(secret: str) -> str:
    return bcrypt_sha256.using(salt=settings.ENCRYPTION_SALT).hash(secret)


def generate_secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


auth_header = HTTPBearer(auto_error=False)
