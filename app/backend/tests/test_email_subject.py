# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""An optional `<name>.subject` template overrides the built-in English subject."""

from jinja2 import DictLoader, Environment

from src.helpers import email as email_module


def _send(monkeypatch, templates: dict) -> dict:
    captured = {}
    monkeypatch.setattr(email_module, "_template_env", Environment(loader=DictLoader(templates), autoescape=True))
    monkeypatch.setattr(email_module, "send_email", lambda **kw: captured.update(kw) or True)
    email_module.send_password_reset_email("ada@example.com", "Ada", "https://app.example/reset")
    return captured


def test_uses_built_in_subject_without_a_subject_template(monkeypatch):
    sent = _send(monkeypatch, {"password_reset.txt": "Body"})
    assert sent["subject"] == "Reset Your Password"


def test_subject_template_overrides_and_renders_context(monkeypatch):
    sent = _send(
        monkeypatch,
        {"password_reset.txt": "Body", "password_reset.subject": "Réinitialisez votre mot de passe {{ app_name }}\n"},
    )
    assert sent["subject"] == f"Réinitialisez votre mot de passe {email_module.APP_NAME}"


def test_blank_subject_template_falls_back(monkeypatch):
    sent = _send(monkeypatch, {"password_reset.txt": "Body", "password_reset.subject": "  \n"})
    assert sent["subject"] == "Reset Your Password"
