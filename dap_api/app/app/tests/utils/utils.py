import random
import string
from typing import Dict, List

from pydantic import EmailStr

from app.config import settings


def random_lower_string(length: int = 32) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> EmailStr:
    return EmailStr(f"{random_lower_string(12)}@{random_lower_string(4)}.com")


def random_coordinate(min_value: int, max_value: int) -> List[float]:
    return [
        round(random.uniform(min_value, max_value), 9),
        round(random.uniform(min_value, max_value), 9)
    ]


def get_admin_header() -> Dict[str, str]:
    return {"Authorization": f"Bearer {settings.ADMIN_USER_SECRET}"}
