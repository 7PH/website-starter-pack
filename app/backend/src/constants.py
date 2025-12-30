# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import os
from enum import StrEnum

USE_TLS = os.environ.get("USE_TLS", "false").lower() == "true"
PUBLIC_PROTOCOL = "https" if USE_TLS else "http"

IS_PROD = os.environ.get("MODE", "PRODUCTION") != "DEVELOPMENT"

PUBLIC_WEBSITE_HOST = os.environ.get("PUBLIC_WEBSITE_HOST", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

# Secret key for hashing user passwords
PASSWORD_HASH_SECRET_KEY = os.environ.get("USERS_PASSWORD_HASH_SECRET_KEY").encode(
    "utf-8"
)

# JWT details
JWT_SECRET_KEY = os.environ.get("TOKEN_HASH_SECRET")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 2

# Minimum length requirement for user passwords
PASSWORD_MIN_LENGTH = 8

# Stripe
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Event log types - core events managed by starterpack
# Projects can extend by creating src/events.py with custom event types


class EventType(StrEnum):
    """Core event types for event logging."""

    # Auth events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_PASSWORD_RESET_REQUEST = "user.password_reset_request"
    USER_PASSWORD_RESET = "user.password_reset"
    USER_EMAIL_VERIFY = "user.email_verify"
    # User events
    USER_PROFILE_UPDATE = "user.profile_update"
    USER_PASSWORD_CHANGE = "user.password_change"
    # Admin events
    ADMIN_IMPERSONATE_START = "admin.impersonate_start"
    ADMIN_IMPERSONATE_STOP = "admin.impersonate_stop"
    ADMIN_USER_UPDATE = "admin.user_update"
    ADMIN_USER_DELETE = "admin.user_delete"


# Metadata for event types (labels and categories for UI)
CORE_EVENT_TYPES = {
    EventType.USER_LOGIN: {"label": "User Login", "category": "auth"},
    EventType.USER_LOGOUT: {"label": "User Logout", "category": "auth"},
    EventType.USER_REGISTER: {"label": "User Register", "category": "auth"},
    EventType.USER_PASSWORD_RESET_REQUEST: {"label": "Password Reset Request", "category": "auth"},
    EventType.USER_PASSWORD_RESET: {"label": "Password Reset", "category": "auth"},
    EventType.USER_EMAIL_VERIFY: {"label": "Email Verified", "category": "auth"},
    EventType.USER_PROFILE_UPDATE: {"label": "Profile Updated", "category": "user"},
    EventType.USER_PASSWORD_CHANGE: {"label": "Password Changed", "category": "user"},
    EventType.ADMIN_IMPERSONATE_START: {"label": "Impersonation Started", "category": "admin"},
    EventType.ADMIN_IMPERSONATE_STOP: {"label": "Impersonation Stopped", "category": "admin"},
    EventType.ADMIN_USER_UPDATE: {"label": "User Updated by Admin", "category": "admin"},
    EventType.ADMIN_USER_DELETE: {"label": "User Deleted by Admin", "category": "admin"},
}
