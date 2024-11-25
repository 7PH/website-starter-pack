import json
from typing import Union

from pydantic import TypeAdapter

from .model.db import *

Main = TypeAdapter(
    Union[
        UserRead,
        UserPreviewRead,
        UserCreate,
        UserLogin,
        UserChangeInfo,
        UserChangePassword,
        UserToken,
        UserTokenUpdate,
        UserPasswordResetRequest,
        UserPasswordResetConfirm,
    ]
)
print(json.dumps(Main.json_schema(), indent=2))
