# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Any context key renders, and a failed send is logged loudly unless mail is simply not set up."""

import logging

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
