
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..constant import PUBLIC_URL
from ..db import get_session
from ..helper import email
from ..model.db import (User, UserChangeInfo, UserChangePassword, UserCreate,
                        UserLogin, UserPasswordResetConfirm,
                        UserPasswordResetRequest, UserRead, UserTokenUpdate)
from ..security import auth

router = APIRouter()

RESET_PASSWORD_BASE_URL = f"{PUBLIC_URL}/reset-password"


@router.post("/users", response_model=UserTokenUpdate, status_code=status.HTTP_201_CREATED)
def register_user(*, session: Session = Depends(get_session), user_create: UserCreate):
    user_create.email = user_create.email.lower()
    if session.execute(select(User).where(User.email == user_create.email)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=user_create.email,
        hashed_password=auth.hash_password(user_create.password),
        first_name=user_create.first_name,
        last_name=user_create.last_name,
    )
    session.add(user)
    session.commit()

    token = auth.generate_token(UserRead.from_orm(user), 7)
    return UserTokenUpdate(
        token_raw=token,
        token_parsed=auth.decode_token(token),
        user=user
    )


@router.post("/users/login", response_model=UserTokenUpdate, status_code=status.HTTP_200_OK)
def login_user(*, session: Session = Depends(get_session), user_login: UserLogin):
    user_login.email = user_login.email.lower()
    user = session.execute(select(User).where(User.email == user_login.email)).scalar_one_or_none()

    if not user or not auth.verify_hashed_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = auth.generate_token(UserRead.from_orm(user), 7)
    return UserTokenUpdate(
        token_raw=token,
        token_parsed=auth.decode_token(token),
        user=user
    )


@router.get("/users/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_user(*, session: Session = Depends(get_session), user_id: int):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def update_user_info(
    *,
    session: Session = Depends(get_session),
    user_id: int,
    user_change_info: UserChangeInfo
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Update only non-None fields
    if user_change_info.first_name is not None:
        user.first_name = user_change_info.first_name

    if user_change_info.last_name is not None:
        user.last_name = user_change_info.last_name

    if user_change_info.email is not None and user.email != user_change_info.email:
        # Check for email conflict
        if session.execute(select(User).where(User.email == user_change_info.email)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        user.email = user_change_info.email
        user.email_confirmed = False  # Reset email confirmation if email changes

    # Commit updates
    session.commit()



@router.put("/users/{user_id}/password", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def update_user_password(*, session: Session = Depends(get_session), user_id: int, user_change_pwd: UserChangePassword):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not auth.verify_hashed_password(user_change_pwd.old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")

    if user_change_pwd.old_password == user_change_pwd.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from the old one")

    user.hashed_password = auth.hash_password(user_change_pwd.new_password)
    session.commit()


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def request_password_reset(*, session: Session = Depends(get_session), pwd_reset: UserPasswordResetRequest):
    user = session.execute(select(User).where(User.email == pwd_reset.email.lower())).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_reset_token = auth.generate_password_reset_token()
    session.commit()

    reset_link = f"{RESET_PASSWORD_BASE_URL}?email={user.email}&token={user.password_reset_token}"
    email.send_email(user.email, "Password Reset Request", f"Use this link to reset your password: {reset_link}")


@router.put("/reset-password", status_code=status.HTTP_200_OK)
def confirm_password_reset(*, session: Session = Depends(get_session), pwd_reset: UserPasswordResetConfirm):
    user = session.execute(
        select(User).where(
            User.email == pwd_reset.email.lower(),
            User.password_reset_token == pwd_reset.token
        )
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token or email")

    user.hashed_password = auth.hash_password(pwd_reset.password)
    user.password_reset_token = None
    session.commit()
