# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from typing import Generic, List, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")


class PaginatedItems(GenericModel, Generic[T]):
    items: List[T]
    has_more: bool
