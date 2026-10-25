# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""The admin event log route forwards every filter to the query."""

import os
from datetime import UTC, datetime
from unittest.mock import patch

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers import admin
from src.helpers.auth import get_current_admin
from src.helpers.db import get_session
from src.schemas.user import UserRead


def test_list_events_forwards_date_range():
    app = FastAPI()
    app.include_router(admin.router)
    app.dependency_overrides[get_session] = lambda: None
    app.dependency_overrides[get_current_admin] = lambda: UserRead(
        id=1, email="a@example.com", is_admin=True, is_premium=False
    )

    with patch.object(admin, "get_events", return_value=([], 0)) as get_events:
        res = TestClient(app).get(
            "/admin/events",
            params={"user_id": 5, "from_date": "2026-10-01T00:00:00Z", "to_date": "2026-10-02T00:00:00Z"},
        )

    assert res.status_code == 200
    filters = get_events.call_args.kwargs["filters"]
    assert filters.user_id == 5
    assert filters.from_date == datetime(2026, 10, 1, tzinfo=UTC)
    assert filters.to_date == datetime(2026, 10, 2, tzinfo=UTC)
