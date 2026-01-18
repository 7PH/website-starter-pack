# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import os
from enum import StrEnum

USE_TLS = os.environ.get("USE_TLS", "false").lower() == "true"
PUBLIC_PROTOCOL = "https" if USE_TLS else "http"

IS_PROD = os.environ.get("MODE", "PRODUCTION") != "DEVELOPMENT"

PUBLIC_WEBSITE_HOST = os.environ.get("PUBLIC_WEBSITE_HOST", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

# JWT details
JWT_SECRET_KEY = os.environ.get("TOKEN_HASH_SECRET")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 2

# Minimum length requirement for user passwords
PASSWORD_MIN_LENGTH = 8

# Stripe
STRIPE_ENABLED = os.environ.get("STRIPE_ENABLED", "false").lower() == "true"
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Organizations
ORGANIZATIONS_ENABLED = os.environ.get("ORGANIZATIONS_ENABLED", "false").lower() == "true"
ORG_MAX_PER_USER = int(os.environ.get("ORG_MAX_PER_USER", "1"))
ORG_MAX_MEMBERS = int(os.environ.get("ORG_MAX_MEMBERS", "50"))
ORG_STRIPE_PRICE_IDS = [
    p.strip() for p in os.environ.get("ORG_STRIPE_PRICE_IDS", "").split(",") if p.strip()
]

# LLM Integration
LLM_ENABLED = os.environ.get("LLM_ENABLED", "false").lower() == "true"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_BASE = os.environ.get("LLM_API_BASE", "")

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
    # Organization events
    ORG_CREATED = "org.created"
    ORG_UPDATED = "org.updated"
    ORG_DELETED = "org.deleted"
    ORG_MEMBER_ADDED = "org.member_added"
    ORG_MEMBER_REMOVED = "org.member_removed"
    ORG_MEMBER_LEFT = "org.member_left"
    ORG_MEMBER_ADMIN_CHANGED = "org.member_admin_changed"
    ORG_MEMBER_PREMIUM_CHANGED = "org.member_premium_changed"
    ORG_SUBSCRIPTION_CREATED = "org.subscription_created"
    ORG_SUBSCRIPTION_CANCELED = "org.subscription_canceled"


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
    EventType.ORG_CREATED: {"label": "Organization Created", "category": "organization"},
    EventType.ORG_UPDATED: {"label": "Organization Updated", "category": "organization"},
    EventType.ORG_DELETED: {"label": "Organization Deleted", "category": "organization"},
    EventType.ORG_MEMBER_ADDED: {"label": "Member Added to Organization", "category": "organization"},
    EventType.ORG_MEMBER_REMOVED: {"label": "Member Removed from Organization", "category": "organization"},
    EventType.ORG_MEMBER_LEFT: {"label": "Member Left Organization", "category": "organization"},
    EventType.ORG_MEMBER_ADMIN_CHANGED: {"label": "Member Admin Status Changed", "category": "organization"},
    EventType.ORG_MEMBER_PREMIUM_CHANGED: {"label": "Member Premium Status Changed", "category": "organization"},
    EventType.ORG_SUBSCRIPTION_CREATED: {"label": "Organization Subscription Created", "category": "organization"},
    EventType.ORG_SUBSCRIPTION_CANCELED: {"label": "Organization Subscription Canceled", "category": "organization"},
}
