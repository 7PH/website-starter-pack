# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the typed event-bus in helpers/hooks.py."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest

from src.helpers import hooks
from src.helpers.hooks import HookEvent, _reset_hooks_for_tests, fire, has_handlers, on


@pytest.fixture(autouse=True)
def reset_hooks():
    _reset_hooks_for_tests()
    yield
    _reset_hooks_for_tests()


@dataclass
class _ToyEvent(HookEvent):
    payload: str = ""
    allow: bool = True
    extra: dict = field(default_factory=dict)


@dataclass
class _OtherEvent(HookEvent):
    seen: int = 0


class TestRegistration:
    def test_no_handlers_returns_event_unchanged(self):
        session = MagicMock()
        event = _ToyEvent(payload="hi")
        result = fire(session, event)
        assert result is event
        assert result.payload == "hi"
        assert result.allow is True

    def test_handler_runs_with_session_and_event(self):
        seen = []

        @on(_ToyEvent)
        def _h(session, event: _ToyEvent):
            seen.append((session, event.payload))

        session = MagicMock()
        fire(session, _ToyEvent(payload="hello"))
        assert seen == [(session, "hello")]

    def test_handlers_run_in_registration_order(self):
        order: list[str] = []

        @on(_ToyEvent)
        def _first(_session, _event):
            order.append("first")

        @on(_ToyEvent)
        def _second(_session, _event):
            order.append("second")

        fire(MagicMock(), _ToyEvent())
        assert order == ["first", "second"]

    def test_mutation_flows_forward(self):
        """Earlier handlers' writes are visible to later ones."""

        @on(_ToyEvent)
        def _set_flag(_session, event: _ToyEvent):
            event.allow = False

        @on(_ToyEvent)
        def _read_flag(_session, event: _ToyEvent):
            event.payload = "denied" if not event.allow else "allowed"

        result = fire(MagicMock(), _ToyEvent(payload="x"))
        assert result.allow is False
        assert result.payload == "denied"

    def test_extra_dict_composes(self):
        @on(_ToyEvent)
        def _h1(_session, event: _ToyEvent):
            event.extra["a"] = 1

        @on(_ToyEvent)
        def _h2(_session, event: _ToyEvent):
            event.extra["b"] = 2

        result = fire(MagicMock(), _ToyEvent())
        assert result.extra == {"a": 1, "b": 2}

    def test_only_matching_event_type_is_dispatched(self):
        toy_seen = 0
        other_seen = 0

        @on(_ToyEvent)
        def _toy(_session, _event):
            nonlocal toy_seen
            toy_seen += 1

        @on(_OtherEvent)
        def _other(_session, _event):
            nonlocal other_seen
            other_seen += 1

        fire(MagicMock(), _ToyEvent())
        assert (toy_seen, other_seen) == (1, 0)
        fire(MagicMock(), _OtherEvent())
        assert (toy_seen, other_seen) == (1, 1)


class TestErrorIsolation:
    def test_handler_exception_is_logged_not_raised(self, caplog):
        @on(_ToyEvent)
        def _bad(_session, _event):
            raise RuntimeError("boom")

        with caplog.at_level("ERROR", logger=hooks.__name__):
            result = fire(MagicMock(), _ToyEvent())

        assert isinstance(result, _ToyEvent)
        assert any("boom" in r.message or "boom" in str(r.exc_info) for r in caplog.records)

    def test_one_failing_handler_does_not_block_siblings(self):
        seen: list[str] = []

        @on(_ToyEvent)
        def _first(_session, _event):
            seen.append("first")

        @on(_ToyEvent)
        def _bad(_session, _event):
            raise RuntimeError("boom")

        @on(_ToyEvent)
        def _third(_session, _event):
            seen.append("third")

        fire(MagicMock(), _ToyEvent())
        assert seen == ["first", "third"]


class TestHasHandlers:
    def test_returns_false_when_no_handlers(self):
        assert has_handlers(_ToyEvent) is False

    def test_returns_true_after_registration(self):
        @on(_ToyEvent)
        def _h(_session, _event):
            pass

        assert has_handlers(_ToyEvent) is True

    def test_independent_per_event_type(self):
        @on(_OtherEvent)
        def _h(_session, _event):
            pass

        assert has_handlers(_OtherEvent) is True
        assert has_handlers(_ToyEvent) is False
