from pydantic import BaseModel, Field
from typing import Optional


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=5000)
    important: bool = Field(False)


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=5000)
    important: Optional[bool] = Field(None)