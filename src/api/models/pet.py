from pydantic import BaseModel, Field


class Category(BaseModel):
    id: int | None = None
    name: str | None = None


class Tag(BaseModel):
    id: int | None = None
    name: str | None = None


class Pet(BaseModel):
    id: int | None = None
    name: str
    status: str = Field(pattern="^(available|pending|sold)$")
    category: Category | None = None
    photoUrls: list[str] = []
    tags: list[Tag] = []