import base64
import secrets


def generate_hash(secret: str) -> str:
    return str(base64.urlsafe_b64encode(bytes(secret, "utf-8")), "utf-8")


def generate_secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
