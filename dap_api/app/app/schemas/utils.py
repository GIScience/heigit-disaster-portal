from typing import Any, List, Dict

from pydantic import BaseModel, Field


class CollectionMetadata(BaseModel):
    id: str
    title: str
    description: str
    links: List[Dict[str, Any]] = []


class BadRequestResponse(BaseModel):
    code: int = Field(..., title="Error code", description="Internal error code providing details on the error source")
    message: str = Field(..., title="Error message", description="Error description")


class HttpErrorResponse(BaseModel):
    detail: str = Field(..., title="Error detail", description="Detailed error message")
