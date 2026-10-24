# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Permission tests for the CMS editor role: plain user vs editor vs admin."""

import os
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.controllers import cms_editors
from src.helpers.auth import get_current_user
from src.helpers.cms_auth import get_current_cms_editor
from src.helpers.db import get_session
from src.models.cms import CmsEditorBase
from src.models.user import UserBase
from src.schemas.user import UserRead

ADMIN, EDITOR, USER = 1, 2, 3


def _db_user(user_id: int, is_admin: bool = False) -> UserBase:
    return UserBase(id=user_id, email=f"u{user_id}@example.com", is_admin=is_admin, deleted_at=None)


class FakeSession:
    """Just enough of a Session for these routes: get/add/delete keyed by primary key."""

    def __init__(self):
        self.users = {ADMIN: _db_user(ADMIN, is_admin=True), EDITOR: _db_user(EDITOR), USER: _db_user(USER)}
        self.editors = {EDITOR: CmsEditorBase(user_id=EDITOR, created_at=datetime.now(UTC))}
        self.commits = 0

    def commit(self):
        self.commits += 1

    def get(self, model, key):
        return (self.users if model is UserBase else self.editors).get(key)

    def add(self, obj):
        obj.created_at = datetime.now(UTC)
        self.editors[obj.user_id] = obj

    def delete(self, obj):
        del self.editors[obj.user_id]

    def execute(self, _query):
        rows = [
            SimpleNamespace(user_id=e.user_id, email=self.users[e.user_id].email, created_at=e.created_at)
            for e in self.editors.values()
        ]
        return MagicMock(all=MagicMock(return_value=rows))


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def client_as(session):
    app = FastAPI()
    app.include_router(cms_editors.router)

    # Stands in for the CMS content routes, which all depend on get_current_cms_editor.
    @app.get("/cms/editor-only")
    def editor_only(user: UserRead = Depends(get_current_cms_editor)):
        return {"ok": True}

    app.dependency_overrides[get_session] = lambda: session

    def make(user_id: int) -> TestClient:
        db_user = session.users[user_id]
        app.dependency_overrides[get_current_user] = lambda: UserRead(
            id=user_id, email=db_user.email, is_admin=db_user.is_admin, is_premium=False
        )
        return TestClient(app)

    with patch.object(cms_editors, "log_event"):
        yield make


@pytest.mark.parametrize(("user_id", "expected"), [(ADMIN, True), (EDITOR, True), (USER, False)])
def test_me(client_as, user_id, expected):
    assert client_as(user_id).get("/cms/me").json() == {"is_editor": expected}


@pytest.mark.parametrize(("user_id", "status"), [(ADMIN, 200), (EDITOR, 200), (USER, 403)])
def test_editor_dependency(client_as, user_id, status):
    assert client_as(user_id).get("/cms/editor-only").status_code == status


@pytest.mark.parametrize("user_id", [EDITOR, USER])
def test_managing_editors_is_admin_only(client_as, user_id):
    client = client_as(user_id)
    assert client.get("/cms/editors").status_code == 403
    assert client.put(f"/cms/editors/{USER}").status_code == 403
    assert client.delete(f"/cms/editors/{EDITOR}").status_code == 403


def test_admin_lists_editors(client_as):
    [editor] = client_as(ADMIN).get("/cms/editors").json()
    assert editor["user_id"] == EDITOR
    assert editor["email"] == "u2@example.com"


def test_admin_grants_and_revokes(client_as):
    # client_as() switches the user of the whole app, so call it before each request.
    assert client_as(ADMIN).put(f"/cms/editors/{USER}").status_code == 200
    assert client_as(ADMIN).put(f"/cms/editors/{USER}").status_code == 200  # idempotent
    assert client_as(USER).get("/cms/editor-only").status_code == 200

    assert client_as(ADMIN).delete(f"/cms/editors/{USER}").status_code == 204
    assert client_as(ADMIN).delete(f"/cms/editors/{USER}").status_code == 204  # idempotent
    assert client_as(USER).get("/cms/editor-only").status_code == 403


def test_grant_unknown_user_404(client_as):
    assert client_as(ADMIN).put("/cms/editors/999").status_code == 404


def test_grant_and_revoke_commit_once_each(client_as, session):
    client_as(ADMIN).put(f"/cms/editors/{USER}")
    client_as(ADMIN).put(f"/cms/editors/{USER}")
    client_as(ADMIN).delete(f"/cms/editors/{USER}")
    assert session.commits == 2


def test_grant_and_revoke_are_logged(client_as):
    client = client_as(ADMIN)
    client.put(f"/cms/editors/{USER}")
    client.put(f"/cms/editors/{USER}")
    client.delete(f"/cms/editors/{USER}")
    changes = [c.kwargs["details"]["changes"]["cms_editor"] for c in cms_editors.log_event.call_args_list]
    assert changes == [{"from": False, "to": True}, {"from": True, "to": False}]
