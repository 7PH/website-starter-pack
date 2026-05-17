# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Email helper module with Jinja2 template support.
Provides functions for sending transactional emails via Mailgun.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

logger = logging.getLogger(__name__)


@contextmanager
def swallow_email_errors():
    """Run a send_*_email() call without bubbling exceptions.

    Use when an email failure (e.g. Mailgun unconfigured in dev) shouldn't
    block the user flow. Failures are logged so ops can spot real outages.
    """
    try:
        yield
    except Exception as e:
        logger.warning("Email send failed: %s", e)

# Configuration
MAILGUN_ENABLED = bool(os.environ.get("MAILGUN_API_KEY"))
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "")
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "")
MAILGUN_FROM_NAME = os.environ.get("MAILGUN_FROM_NAME", "App")
MAILGUN_FROM_EMAIL = f"no-reply@{MAILGUN_DOMAIN}" if MAILGUN_DOMAIN else ""
MAILGUN_API_BASEURL = f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}"

PUBLIC_URL = os.environ.get("PUBLIC_URL", "")
APP_NAME = os.environ.get("APP_NAME", "App")

# Initialize Jinja2 template environment
_template_dir = Path(__file__).parent.parent / "templates" / "email"
_template_env: Environment | None = None

if _template_dir.exists():
    _template_env = Environment(
        loader=FileSystemLoader(str(_template_dir)),
        autoescape=True,
    )


def _render_template(name: str, **context) -> str | None:
    """Render a template by name with the default context, or None if missing."""
    if _template_env is None:
        return None
    try:
        template: Template = _template_env.get_template(name)
    except TemplateNotFound:
        return None
    return template.render(public_url=PUBLIC_URL, app_name=APP_NAME, **context)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    raise_on_error: bool = True,
) -> bool:
    """
    Send an email via Mailgun.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        raise_on_error: Whether to raise an exception on error

    Returns:
        True if email was sent successfully, False otherwise
    """
    if not MAILGUN_ENABLED:
        logger.warning(f"Email disabled, skipping: {to_email} - {subject}")
        if raise_on_error:
            raise ValueError("Email service not configured (MAILGUN_API_KEY missing)")
        return False

    data = {
        "from": f"{MAILGUN_FROM_NAME} <{MAILGUN_FROM_EMAIL}>",
        "to": [to_email],
        "subject": subject,
        "text": body,
    }

    if html_body:
        data["html"] = html_body

    try:
        response = requests.post(
            f"{MAILGUN_API_BASEURL}/messages",
            auth=("api", MAILGUN_API_KEY),
            data=data,
            timeout=30,
        )

        if response.status_code != 200:
            logger.error(f"Mailgun error: {response.status_code} - {response.text}")
            if raise_on_error:
                raise ValueError(f"Failed to send email: {response.status_code}")
            return False

        return True

    except requests.RequestException as e:
        logger.error(f"Mailgun request error: {e}")
        if raise_on_error:
            raise
        return False


def _send_templated_email(
    *,
    to_email: str,
    subject: str,
    template_basename: str,
    context: dict,
    text_fallback: str | None,
    raise_on_error: bool = True,
) -> bool:
    """Render the templated HTML+text bodies and send. Falls back to ``text_fallback`` text-only.

    If ``text_fallback`` is None and the template is missing, raises — for emails
    where shipping a plain-text default would be wrong (e.g. account deletion).
    """
    html_body = _render_template(f"{template_basename}.html", **context)
    text_body = _render_template(f"{template_basename}.txt", **context)
    if text_body is None:
        if text_fallback is None:
            raise RuntimeError(f"{template_basename} email template is missing")
        text_body = text_fallback
    return send_email(
        to_email=to_email,
        subject=subject,
        body=text_body,
        html_body=html_body,
        raise_on_error=raise_on_error,
    )


def send_password_reset_email(to_email: str, username: str, reset_link: str) -> bool:
    return _send_templated_email(
        to_email=to_email,
        subject="Reset Your Password",
        template_basename="password_reset",
        context={"username": username, "reset_link": reset_link},
        text_fallback=(
            f"Hello {username},\n\n"
            f"We received a request to reset your password. Click the link below:\n"
            f"{reset_link}\n\n"
            f"This link will expire in 1 hour.\n\n"
            f"If you didn't request this, you can ignore this email.\n"
        ),
    )


def send_email_verification_email(to_email: str, username: str, verification_link: str) -> bool:
    return _send_templated_email(
        to_email=to_email,
        subject="Verify Your Email Address",
        template_basename="email_verification",
        context={"username": username, "verification_link": verification_link},
        text_fallback=(
            f"Hello {username},\n\n"
            f"Thank you for signing up! Please verify your email by clicking the link below:\n"
            f"{verification_link}\n\n"
            f"This link will expire in 24 hours.\n"
        ),
    )


def send_organization_invitation_email(
    to_email: str,
    organization_name: str,
    inviter_name: str | None,
    invitation_link: str,
    is_admin_invite: bool,
) -> bool:
    role = "Owner" if is_admin_invite else "Member"
    who = f"{inviter_name} has" if inviter_name else "You have been"
    return _send_templated_email(
        to_email=to_email,
        subject=f"You've been invited to join {organization_name}",
        template_basename="organization_invitation",
        context={
            "organization_name": organization_name,
            "inviter_name": inviter_name,
            "invitation_link": invitation_link,
            "is_admin_invite": is_admin_invite,
        },
        text_fallback=(
            f"Hello,\n\n"
            f"{who} invited you to join {organization_name} as a {role}.\n\n"
            f"Accept or decline the invitation here:\n"
            f"{invitation_link}\n\n"
            f"If you weren't expecting this, you can ignore this email.\n"
        ),
        raise_on_error=False,
    )


def send_account_deletion_email(to_email: str, username: str, confirmation_link: str) -> bool:
    return _send_templated_email(
        to_email=to_email,
        subject="Confirm Account Deletion",
        template_basename="account_deletion",
        context={"username": username, "confirmation_link": confirmation_link},
        text_fallback=None,  # No fallback: template is required.
    )


def send_email_change_email(to_email: str, username: str, confirmation_link: str) -> bool:
    return _send_templated_email(
        to_email=to_email,
        subject="Confirm Your New Email Address",
        template_basename="email_change",
        context={"username": username, "confirmation_link": confirmation_link},
        text_fallback=(
            f"Hello {username},\n\n"
            f"You requested to change your email address to this one. Click the link below to confirm:\n"
            f"{confirmation_link}\n\n"
            f"This link will expire in 48 hours.\n\n"
            f"If you didn't request this change, you can ignore this email.\n"
        ),
    )
