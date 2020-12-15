import random
import string
from typing import Tuple

from geojson_pydantic.utils import NumType


def random_lower_string(length: int = 32) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    return f"{random_lower_string(12)}@{random_lower_string(4)}.com"


def random_coordinate(min_value: int, max_value: int) -> Tuple[NumType, NumType]:
    return round(random.uniform(min_value, max_value), 9),\
           round(random.uniform(min_value, max_value), 9)
