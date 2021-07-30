import random
import string
from typing import Tuple, Dict

from geojson_pydantic.types import NumType

from app.config import settings


def random_lower_string(length: int = 32) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    return f"{random_lower_string(12)}@{random_lower_string(4)}.com"


def random_coordinate(min_value: int, max_value: int) -> Tuple[NumType, NumType]:
    return round(random.uniform(min_value, max_value), 9), \
           round(random.uniform(min_value, max_value), 9)


def get_admin_header() -> Dict[str, str]:
    return {"Authorization": f"Bearer {settings.ADMIN_USER_SECRET}"}
