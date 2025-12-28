# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..constants import PUBLIC_URL
from ..helpers.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..helpers.db import get_session
from ..crud.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    is_email_taken,
    update_user,
)
from ..models.user import (
    UserBase,
    UserChangeInfo,
    UserChangePassword,
    UserCreate,
    UserRead,
    UserTokenUpdate,
)

router = APIRouter()

RESET_PASSWORD_BASE_URL = f"{PUBLIC_URL}/reset-password"


@router.post(
    "/users", response_model=UserTokenUpdate, status_code=status.HTTP_201_CREATED
)
def register_user(*, session: Session = Depends(get_session), user_create: UserCreate):
    user_create.email = user_create.email.lower()
    if is_email_taken(session, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = UserBase(
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        first_name=user_create.first_name,
        last_name=user_create.last_name,
    )
    create_user(session, user)

    token = create_access_token(UserRead.model_validate(user))

    return UserTokenUpdate(
        access_token=token.access_token,
        token_parsed=token.token_parsed,
        user=user,
    )


@router.post(
    "/users/login", response_model=UserTokenUpdate, status_code=status.HTTP_200_OK
)
def login_user(
    *,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # Lowercase the username (email in this case) for case-insensitive login
    email = form_data.username.lower()
    password = form_data.password

    user = get_user_by_email(session, email)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    return create_access_token(UserRead.model_validate(user))


@router.get("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_me(*, current_user: UserRead = Depends(get_current_user)):
    """
    Get the details of the currently authenticated user.
    """
    return current_user


@router.get("/users/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_user(
    *,
    session: Session = Depends(get_session),
    user_id: int,
    current_user: UserRead = Depends(get_current_user),
):
    """
    Get user details by ID. Restricted to authenticated users.
    """
    user = get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.patch("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_me(
    *,
    session: Session = Depends(get_session),
    user_change_info: UserChangeInfo,
    current_user: UserRead = Depends(get_current_user),
):
    """
    Update the details of the currently authenticated user.
    """
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_change_info.first_name is not None:
        user.first_name = user_change_info.first_name

    if user_change_info.last_name is not None:
        user.last_name = user_change_info.last_name

    if user_change_info.email is not None and user.email != user_change_info.email:
        if is_email_taken(session, user_change_info.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
            )
        user.email = user_change_info.email
        user.email_confirmed = False

    update_user(session, user)

    return UserRead.model_validate(user)


@router.put(
    "/users/me/password",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def update_my_password(
    *,
    session: Session = Depends(get_session),
    user_change_pwd: UserChangePassword,
    current_user: UserRead = Depends(get_current_user),
):
    """
    Update the password of the currently authenticated user.
    """
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not verify_password(user_change_pwd.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password"
        )

    if user_change_pwd.old_password == user_change_pwd.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the old one",
        )

    user.hashed_password = hash_password(user_change_pwd.new_password)
    update_user(session, user)

    return UserRead.model_validate(user)
