from src._core.resources.users.model import UserBase


class User(UserBase):
    """Overriding UserBase with any custom fields"""

    __mapper_args__ = {"polymorphic_identity": "user"}
