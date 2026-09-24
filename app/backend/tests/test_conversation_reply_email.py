# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""An admin reply emails the user who opened the conversation."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.controllers import conversations as conv_module
from src.helpers import email as email_module


def _reply(monkeypatch, created_by):
    conversation = SimpleNamespace(id=7, is_closed=False, created_by=created_by)
    sent = []
    monkeypatch.setattr(conv_module, "_get_conversation_or_404", lambda _s, _id: conversation)
    monkeypatch.setattr(conv_module, "add_message", lambda **_kw: SimpleNamespace(id=1))
    monkeypatch.setattr(conv_module, "log_event", lambda *_a, **_kw: None)
    monkeypatch.setattr(conv_module, "_message_to_read", lambda m: m)
    monkeypatch.setattr(conv_module, "send_conversation_reply_email", lambda **kw: sent.append(kw))
    conv_module.admin_send_message(
        session=MagicMock(),
        request=MagicMock(),
        admin=SimpleNamespace(id=1),
        conversation_id=7,
        data=SimpleNamespace(content="Hi"),
    )
    return sent


def _user(**overrides):
    return SimpleNamespace(**{"email": "ada@example.com", "first_name": "Ada", "deleted_at": None, **overrides})


def test_emails_conversation_creator(monkeypatch):
    sent = _reply(monkeypatch, _user())
    assert sent == [{"to_email": "ada@example.com", "username": "Ada", "conversation_id": 7}]


@pytest.mark.parametrize(
    "created_by",
    [None, _user(email=None), _user(deleted_at=datetime.now(UTC))],
    ids=["creator-gone", "no-email", "deleted-user"],
)
def test_skips_users_who_cannot_receive_email(monkeypatch, created_by):
    assert _reply(monkeypatch, created_by) == []


def test_email_links_to_the_conversation(monkeypatch):
    captured = {}
    monkeypatch.setattr(email_module, "PUBLIC_URL", "https://app.example")
    monkeypatch.setattr(email_module, "send_email", lambda **kw: captured.update(kw) or True)
    email_module.send_conversation_reply_email("ada@example.com", "Ada", 7)
    assert "https://app.example/messages/7" in captured["body"]
    assert "https://app.example/messages/7" in captured["html_body"]
