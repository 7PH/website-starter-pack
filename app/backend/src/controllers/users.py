# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..constants import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, PUBLIC_URL, EventType
from ..crud.event_logs import log_event
from ..crud.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    is_email_taken,
    update_user,
)
from ..helpers import stripe as stripe_helper
from ..helpers.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    oauth2_scheme,
    verify_password,
)
from ..helpers.db import get_session
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
def register_user(*, request: Request, session: Session = Depends(get_session), user_create: UserCreate):
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

    # Create Stripe customer and free subscription for the new user
    if stripe_helper.is_enabled():
        user.stripe_id = stripe_helper.sync_customer(
            user_id=user.id,
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
        )
        stripe_helper.create_subscription(user.stripe_id)
        update_user(session, user)

    token = create_access_token(UserRead.model_validate(user))

    # Log the registration event
    log_event(session, action=EventType.USER_REGISTER, user_id=user.id, request=request)

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
    request: Request,
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

    # Log the login event
    log_event(session, action=EventType.USER_LOGIN, user_id=user.id, request=request)

    return create_access_token(UserRead.model_validate(user))


@router.get("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_me(*, current_user: UserRead = Depends(get_current_user)):
    """
    Get the details of the currently authenticated user.
    """
    return current_user


@router.post("/users/me/token", response_model=UserTokenUpdate, status_code=status.HTTP_200_OK)
def refresh_token(
    *,
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    """
    Refresh the current user's token.
    Rate limited: won't issue new token if current one is less than 5 minutes old.
    """
    # Decode current token to check creation time
    payload = decode_access_token(token)

    # Check if token was issued less than 5 minutes ago
    token_exp = payload.get("exp", 0)
    token_created = token_exp - (JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    now = datetime.now(UTC).timestamp()

    if now - token_created < 300:  # 5 minutes
        # Return current token info without generating new one
        return UserTokenUpdate(
            access_token=token,
            token_parsed=dict(
                user=current_user,
                created_at=datetime.fromtimestamp(token_created, tz=UTC),
                expires_at=datetime.fromtimestamp(token_exp, tz=UTC),
            ),
            user=current_user,
        )

    # Fetch fresh user data and issue new token
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return create_access_token(UserRead.model_validate(user))


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
    request: Request,
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

    # Log profile update
    log_event(session, action=EventType.USER_PROFILE_UPDATE, user_id=user.id, request=request)

    return UserRead.model_validate(user)


@router.put(
    "/users/me/password",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def update_my_password(
    *,
    request: Request,
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

    # Log password change
    log_event(session, action=EventType.USER_PASSWORD_CHANGE, user_id=user.id, request=request)

    return UserRead.model_validate(user)
