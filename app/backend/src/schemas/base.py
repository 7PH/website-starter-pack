# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from pydantic import BaseModel


class PaginatedItems[T](BaseModel):
    items: list[T]
    has_more: bool
