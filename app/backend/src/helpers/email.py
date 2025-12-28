# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Email helper module with Jinja2 template support.
Provides functions for sending transactional emails via Mailgun.
"""

import os
import logging
from typing import Optional
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

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
_template_env: Optional[Environment] = None

if _template_dir.exists():
    _template_env = Environment(
        loader=FileSystemLoader(str(_template_dir)),
        autoescape=True,
    )


def _get_template(name: str) -> Optional[str]:
    """Load a template by name. Returns None if not found."""
    if _template_env is None:
        return None
    try:
        template = _template_env.get_template(name)
        return template
    except TemplateNotFound:
        return None


def _render_template(name: str, **context) -> Optional[str]:
    """Render a template with the given context."""
    template = _get_template(name)
    if template is None:
        return None

    # Add default context
    default_context = {
        "public_url": PUBLIC_URL,
        "app_name": APP_NAME,
    }

    return template.render(**default_context, **context)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
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


def send_password_reset_email(
    to_email: str,
    username: str,
    reset_link: str,
) -> bool:
    """
    Send a password reset email.

    Args:
        to_email: Recipient email address
        username: User's display name
        reset_link: Password reset URL

    Returns:
        True if email was sent successfully
    """
    context = {
        "username": username,
        "reset_link": reset_link,
    }

    # Try to render templates
    html_body = _render_template("password_reset.html", **context)
    text_body = _render_template("password_reset.txt", **context)

    # Fallback if templates not available
    if text_body is None:
        text_body = f"""Hello {username},

We received a request to reset your password. Click the link below:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, you can ignore this email.
"""

    return send_email(
        to_email=to_email,
        subject="Reset Your Password",
        body=text_body,
        html_body=html_body,
    )


def send_email_verification_email(
    to_email: str,
    username: str,
    verification_link: str,
) -> bool:
    """
    Send an email verification email.

    Args:
        to_email: Recipient email address
        username: User's display name
        verification_link: Email verification URL

    Returns:
        True if email was sent successfully
    """
    context = {
        "username": username,
        "verification_link": verification_link,
    }

    html_body = _render_template("email_verification.html", **context)
    text_body = _render_template("email_verification.txt", **context)

    if text_body is None:
        text_body = f"""Hello {username},

Thank you for signing up! Please verify your email by clicking the link below:
{verification_link}

This link will expire in 24 hours.
"""

    return send_email(
        to_email=to_email,
        subject="Verify Your Email Address",
        body=text_body,
        html_body=html_body,
    )


def send_welcome_email(
    to_email: str,
    username: str,
) -> bool:
    """
    Send a welcome email after registration.

    Args:
        to_email: Recipient email address
        username: User's display name

    Returns:
        True if email was sent successfully
    """
    context = {
        "username": username,
    }

    html_body = _render_template("welcome.html", **context)
    text_body = _render_template("welcome.txt", **context)

    if text_body is None:
        text_body = f"""Hello {username},

Welcome to {APP_NAME}! Your account has been created successfully.

Get started: {PUBLIC_URL}
"""

    return send_email(
        to_email=to_email,
        subject=f"Welcome to {APP_NAME}!",
        body=text_body,
        html_body=html_body,
        raise_on_error=False,  # Welcome emails are not critical
    )
