# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the bug-report feature: URL stripping, account-age gate, schema validation, per-subtype rate limiter."""

import os

# helpers.db reads APP_DB_* at import time; seed dummies before importing src.*
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.helpers.account import assert_min_account_age
from src.helpers.bug_report import strip_url_query_in_body
from src.helpers.ratelimit import ensure_rate_limit
from src.schemas.conversation import ConversationCreate


class TestStripUrlQueryInBody:
    """strip_url_query_in_body truncates URLs at '?' or '#' on the auto-captured context line."""

    def test_strips_query_string(self):
        body = "**Description**\nBug\n\n---\n_Auto-captured context:_\n- URL: https://example.com/path?token=abc\n- Viewport: 1440×900\n"
        result = strip_url_query_in_body(body)
        assert "- URL: https://example.com/path\n" in result
        assert "token=abc" not in result

    def test_strips_fragment(self):
        body = "- URL: https://example.com/path#secret"
        assert strip_url_query_in_body(body) == "- URL: https://example.com/path"

    def test_strips_whichever_comes_first(self):
        # '#' before '?' — truncate at '#'
        body = "- URL: https://example.com/path#frag?tail"
        assert strip_url_query_in_body(body) == "- URL: https://example.com/path"

    def test_idempotent(self):
        clean = "- URL: https://example.com/path"
        assert strip_url_query_in_body(clean) == clean
        assert strip_url_query_in_body(strip_url_query_in_body(clean)) == clean

    def test_preserves_other_lines(self):
        body = "**Description**\nfoo\n- URL: /a?b=1\n- User-agent: Mozilla\n"
        result = strip_url_query_in_body(body)
        assert "**Description**" in result
        assert "- User-agent: Mozilla" in result
        assert "- URL: /a\n" in result

    def test_no_url_line_unchanged(self):
        body = "no context here\njust text\n"
        assert strip_url_query_in_body(body) == body

    def test_only_matches_context_line(self):
        # An arbitrary mention of "URL" in the description should not be touched.
        body = "i visited a URL: https://example.com/x?y=1 and it broke"
        assert strip_url_query_in_body(body) == body


class TestAssertMinAccountAge:
    """assert_min_account_age raises 429 for accounts younger than the threshold."""

    def _patch_user(self, monkeypatch, *, minutes_ago: int | None):
        from src.helpers import account as account_module

        created_at = None if minutes_ago is None else datetime.now(UTC) - timedelta(minutes=minutes_ago)
        user = SimpleNamespace(created_at=created_at)
        monkeypatch.setattr(account_module, "get_user_by_id", lambda _session, _user_id: user)

    def test_rejects_young_account(self, monkeypatch):
        self._patch_user(monkeypatch, minutes_ago=5)
        with pytest.raises(HTTPException) as exc:
            assert_min_account_age(session=None, user_id=1, min_minutes=10)
        assert exc.value.status_code == 429

    def test_accepts_old_account(self, monkeypatch):
        self._patch_user(monkeypatch, minutes_ago=60)
        assert_min_account_age(session=None, user_id=1, min_minutes=10)

    def test_accepts_account_exactly_at_threshold(self, monkeypatch):
        self._patch_user(monkeypatch, minutes_ago=10)
        assert_min_account_age(session=None, user_id=1, min_minutes=10)

    def test_null_created_at_does_not_raise(self, monkeypatch):
        self._patch_user(monkeypatch, minutes_ago=None)
        assert_min_account_age(session=None, user_id=1, min_minutes=10)

    def test_missing_user_does_not_raise(self, monkeypatch):
        from src.helpers import account as account_module

        monkeypatch.setattr(account_module, "get_user_by_id", lambda _s, _id: None)
        assert_min_account_age(session=None, user_id=999, min_minutes=10)


class TestConversationCreateValidation:
    """ConversationCreate accepts the union of core + project subtypes and rejects unknown ones."""

    def test_accepts_known_subtype(self):
        c = ConversationCreate(subject="hi", content="hello", subtype="bug_report")
        # Pydantic coerces the string into the enum member.
        assert c.subtype == "bug_report"
        assert c.subtype.value == "bug_report"

    def test_accepts_null_subtype(self):
        c = ConversationCreate(subject="hi", content="hello", subtype=None)
        assert c.subtype is None

    def test_rejects_unknown_subtype(self):
        with pytest.raises(ValidationError):
            ConversationCreate(subject="hi", content="hello", subtype="definitely_not_allowed")

    def test_content_uses_global_cap(self):
        c = ConversationCreate(subject="hi", content="x" * 10000, subtype="bug_report")
        assert len(c.content) == 10000
        with pytest.raises(ValidationError):
            ConversationCreate(subject="hi", content="x" * 10001, subtype="bug_report")


class TestPerSubtypeRateLimit:
    """ensure_rate_limit keeps independent counters when the action encodes the subtype.

    The autouse `_ratelimit_store` fixture (conftest) gives each test a fresh
    in-memory fake Redis, so no manual reset is needed.
    """

    def test_bug_report_and_feature_request_counters_independent(self):
        # Burn the bug-report quota (5/hour).
        for _ in range(5):
            ensure_rate_limit(
                action="conversation-create:bug_report",
                quota=5,
                key="1",
                duration_minutes=60,
            )
        with pytest.raises(HTTPException) as exc:
            ensure_rate_limit(
                action="conversation-create:bug_report",
                quota=5,
                key="1",
                duration_minutes=60,
            )
        assert exc.value.status_code == 429

        # feature_request quota for the same user is untouched.
        ensure_rate_limit(
            action="conversation-create:feature_request",
            quota=5,
            key="1",
            duration_minutes=60,
        )

    def test_different_users_have_independent_counters(self):
        for _ in range(5):
            ensure_rate_limit(
                action="conversation-create:bug_report",
                quota=5,
                key="1",
                duration_minutes=60,
            )
        # Other user is fine
        ensure_rate_limit(
            action="conversation-create:bug_report",
            quota=5,
            key="2",
            duration_minutes=60,
        )
