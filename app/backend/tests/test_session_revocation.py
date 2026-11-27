# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tokens are checked against the DB: a bumped token_version signs the user out everywhere."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from src.constants import JWT_ALGORITHM, JWT_SECRET_KEY
from src.controllers import admin as admin_controller
from src.controllers import auth as auth_controller
from src.controllers import users as users_controller
from src.crud import users as crud_users
from src.helpers.auth import create_access_token, decode_access_token, get_current_user
from src.helpers.auth_tokens import create_password_reset_token
from src.models.user import UserBase
from src.schemas.admin import AdminUserUpdate
from src.schemas.user import PasswordResetConfirmJWT, UserChangePassword, UserRead


def _row(user_id=1, *, token_version=0, is_admin=False, **kwargs) -> UserBase:
    return UserBase(
        id=user_id,
        email=f"u{user_id}@example.com",
        auth_method="password",
        is_admin=is_admin,
        is_premium=False,
        has_personal_subscription=False,
        email_confirmed=True,
        token_version=token_version,
        custom_data={},
        **kwargs,
    )


def _token(row: UserBase, *, claims_admin: bool = False, **kwargs) -> str:
    read = UserRead.model_validate(row)
    read.is_admin = claims_admin
    return create_access_token(read, token_version=row.token_version, **kwargs).access_token


def _rows(*rows):
    by_id = {r.id: r for r in rows}
    return patch.object(crud_users, "get_user_by_id", side_effect=lambda _s, uid, **_: by_id.get(uid))


def test_current_user_reads_admin_and_email_confirmed_from_db():
    row = _row()
    token = _token(row, claims_admin=True)
    row.email_confirmed = False
    with _rows(row):
        user = get_current_user(token, MagicMock())
    assert user.is_admin is False
    assert user.email_confirmed is False


def test_bumped_token_version_rejects_old_token():
    row = _row()
    token = _token(row)
    row.token_version = 1
    with _rows(row), pytest.raises(HTTPException) as exc:
        get_current_user(token, MagicMock())
    assert exc.value.status_code == 401


def test_token_without_version_claim_matches_default():
    """Sessions issued before the upgrade stay valid."""
    row = _row()
    payload = decode_access_token(_token(row))
    del payload["data"]["token_version"]
    legacy = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    with _rows(row):
        assert get_current_user(legacy, MagicMock()).id == row.id


def test_deleted_user_token_is_rejected():
    token = _token(_row())
    with _rows(), pytest.raises(HTTPException) as exc:
        get_current_user(token, MagicMock())
    assert exc.value.status_code == 401


def test_impersonation_token_dies_when_admin_is_demoted():
    admin, target = _row(1, is_admin=True), _row(2)
    token = create_access_token(
        UserRead.model_validate(admin),
        token_version=target.token_version,
        impersonating_as=UserRead.model_validate(target),
    ).access_token
    with _rows(admin, target):
        assert get_current_user(token, MagicMock()).id == target.id
    admin.is_admin = False
    with _rows(admin, target), pytest.raises(HTTPException):
        get_current_user(token, MagicMock())


def test_refresh_refuses_stale_token_even_inside_cooldown():
    row = _row()
    token = _token(row)
    row.token_version = 1
    with _rows(row), pytest.raises(HTTPException) as exc:
        users_controller.refresh_token(session=MagicMock(), token=token)
    assert exc.value.status_code == 401


def test_refresh_issues_token_with_current_version():
    row = _row(token_version=3)
    payload = decode_access_token(_token(row))
    del payload["iat"]  # minted before iat existed: refreshes right away
    old = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    with (
        _rows(row),
        patch.object(users_controller, "build_user_read_with_orgs", return_value=UserRead.model_validate(row)),
    ):
        fresh = users_controller.refresh_token(session=MagicMock(), token=old)
    assert fresh.access_token != old
    assert decode_access_token(fresh.access_token)["data"]["token_version"] == 3


def test_password_change_revokes_and_returns_fresh_token():
    row = _row(hashed_password="hash")
    with (
        patch.object(users_controller, "get_user_or_404", return_value=row),
        patch.object(users_controller, "verify_password", return_value=True),
        patch.object(users_controller, "update_user"),
        patch.object(users_controller, "log_event"),
        patch("src.helpers.auth.build_user_read_with_orgs", return_value=UserRead.model_validate(row)),
    ):
        result = users_controller.update_my_password(
            request=MagicMock(),
            session=MagicMock(),
            user_change_pwd=UserChangePassword(old_password="old-password", new_password="new-password"),
            current_user=MagicMock(id=row.id),
        )
    assert row.token_version == 1
    assert decode_access_token(result.access_token)["data"]["token_version"] == 1


def test_reset_link_works_once():
    row = _row(hashed_password="hash")
    body = PasswordResetConfirmJWT(
        token=create_password_reset_token(row.id, row.token_version), password="new-password"
    )
    with (
        patch.object(auth_controller, "get_user_or_404", return_value=row),
        patch.object(auth_controller, "update_user"),
        patch.object(auth_controller, "log_event"),
    ):
        auth_controller.reset_password(request=MagicMock(), session=MagicMock(), body=body)
        assert row.token_version == 1
        with pytest.raises(HTTPException) as exc:
            auth_controller.reset_password(request=MagicMock(), session=MagicMock(), body=body)
    assert exc.value.status_code == 400


def test_admin_demotion_revokes_sessions():
    row = _row(is_admin=True)
    with (
        patch.object(admin_controller, "get_user_or_404", return_value=row),
        patch.object(admin_controller, "update_user"),
        patch.object(admin_controller, "log_event"),
    ):
        admin_controller.update_user_by_admin(
            session=MagicMock(),
            request=MagicMock(),
            admin=MagicMock(),
            user_id=row.id,
            user_update=AdminUserUpdate(is_admin=False),
        )
    assert row.token_version == 1
