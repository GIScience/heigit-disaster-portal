from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class BaseTable:
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(self, cls) -> str:
        return cls.__name__.lower()

    def __init__(self, **kwargs):
        for key in kwargs:
            self.__setattr__(key, kwargs.get(key))
