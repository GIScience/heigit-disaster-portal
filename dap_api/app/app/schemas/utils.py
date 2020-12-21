from typing import Any, List, Dict

from pydantic import BaseModel


class CollectionMetadata(BaseModel):
    id: str
    title: str
    description: str
    links: List[Dict[str, Any]] = []
