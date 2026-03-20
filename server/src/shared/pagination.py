from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.size - 1) // self.size if self.size > 0 else 0
