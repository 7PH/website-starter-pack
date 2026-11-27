# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Email rendering, sending headers, and how failed sends are logged."""

import logging
from unittest.mock import MagicMock

from jinja2 import DictLoader, Environment

from src.helpers import email as email_module


def test_context_keys_that_shadow_parameters_render(monkeypatch):
    monkeypatch.setattr(
        email_module, "_template_env", Environment(loader=DictLoader({"t.txt": "{{ name }} {{ app_name }}"}))
    )
    assert email_module._render_template("t.txt", name="Ada", app_name="Shop") == "Ada Shop"


def test_failed_send_is_logged_with_traceback(caplog):
    with caplog.at_level(logging.WARNING), email_module.swallow_email_errors():
        raise TypeError("broken template")
    record = caplog.records[-1]
    assert record.levelno == logging.ERROR
    assert record.exc_info


def test_missing_mail_service_is_only_a_warning(caplog):
    with caplog.at_level(logging.WARNING), email_module.swallow_email_errors():
        raise email_module.EmailNotConfiguredError("no mail service")
    assert caplog.records[-1].levelno == logging.WARNING


def _post_with(monkeypatch, **kwargs) -> dict:
    monkeypatch.setattr(email_module, "MAILGUN_ENABLED", True)
    post = MagicMock(return_value=MagicMock(status_code=200))
    monkeypatch.setattr(email_module.requests, "post", post)
    email_module.send_email("ada@example.com", "Hi", "Body", **kwargs)
    return post.call_args.kwargs["data"]


def test_reply_to_header_is_sent_when_given(monkeypatch):
    assert _post_with(monkeypatch, reply_to="team@example.com")["h:Reply-To"] == "team@example.com"


def test_no_reply_to_header_by_default(monkeypatch):
    assert "h:Reply-To" not in _post_with(monkeypatch)
