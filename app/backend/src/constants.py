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

# Shared secret for the /v1/internal/* routes (token minting, user seeding).
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", "")
# A key alone can't expose these auth-bypassing routes in prod: .env.template ships one.
INTERNAL_API_ENABLED = bool(INTERNAL_API_KEY) and (
    not IS_PROD or os.environ.get("INTERNAL_API_ENABLED", "false").lower() == "true"
)

# Minimum length requirement for user passwords
PASSWORD_MIN_LENGTH = 8

# Stripe
STRIPE_ENABLED = os.environ.get("STRIPE_ENABLED", "false").lower() == "true"
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
USER_STRIPE_PRICE_IDS = [p.strip() for p in os.environ.get("USER_STRIPE_PRICE_IDS", "").split(",") if p.strip()]

# Organizations
ORGANIZATIONS_ENABLED = os.environ.get("ORGANIZATIONS_ENABLED", "false").lower() == "true"
ORG_MAX_PER_USER = int(os.environ.get("ORG_MAX_PER_USER", "1"))
ORG_MAX_MEMBERS = int(os.environ.get("ORG_MAX_MEMBERS", "50"))
ORG_STRIPE_PRICE_IDS = [p.strip() for p in os.environ.get("ORG_STRIPE_PRICE_IDS", "").split(",") if p.strip()]
ORG_SELF_SERVICE_SUBSCRIPTIONS = os.environ.get("ORG_SELF_SERVICE_SUBSCRIPTIONS", "true").lower() == "true"
ORG_SELF_SERVICE_CREATION = os.environ.get("ORG_SELF_SERVICE_CREATION", "true").lower() == "true"
ORG_INVITATIONS_ENABLED = os.environ.get("ORG_INVITATIONS_ENABLED", "false").lower() == "true"
ORG_INVITATION_EXPIRY_DAYS = int(os.environ.get("ORG_INVITATION_EXPIRY_DAYS", "7"))

# Managed account groups (one owner manages many email-less accounts that
# sign in by code). Off by default; sub-apps that need it opt in via the env.
MANAGED_ACCOUNTS_ENABLED = os.environ.get("MANAGED_ACCOUNTS_ENABLED", "false").lower() == "true"
MANAGED_ACCOUNT_GROUP_MAX_PER_USER = int(os.environ.get("MANAGED_ACCOUNT_GROUP_MAX_PER_USER", "20"))
# Total managed accounts an owner can have across all their groups combined.
MANAGED_ACCOUNTS_MAX_PER_USER = int(os.environ.get("MANAGED_ACCOUNTS_MAX_PER_USER", "1000"))

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
    USER_LOGIN_CODE = "user.login_code"
    USER_LOGIN_CODE_FAIL = "user.login_code_fail"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_PASSWORD_RESET_REQUEST = "user.password_reset_request"
    USER_PASSWORD_RESET = "user.password_reset"
    USER_EMAIL_VERIFY = "user.email_verify"
    # User events
    USER_PROFILE_UPDATE = "user.profile_update"
    USER_PASSWORD_CHANGE = "user.password_change"
    USER_DELETE_REQUEST = "user.delete_request"
    USER_DELETE_COMPLETE = "user.delete_complete"
    # Admin events
    ADMIN_IMPERSONATE_START = "admin.impersonate_start"
    ADMIN_IMPERSONATE_STOP = "admin.impersonate_stop"
    ADMIN_USER_UPDATE = "admin.user_update"
    ADMIN_USER_DELETE = "admin.user_delete"
    # Managed account group events (owner-initiated; admin = the group owner)
    MANAGED_GROUP_CREATED = "managed_group.created"
    MANAGED_GROUP_UPDATED = "managed_group.updated"
    MANAGED_GROUP_DELETED = "managed_group.deleted"
    MANAGED_GROUP_TOKEN_ROTATED = "managed_group.token_rotated"
    MANAGED_ACCOUNT_CREATED = "managed_account.created"
    MANAGED_ACCOUNT_UPDATED = "managed_account.updated"
    MANAGED_ACCOUNT_DELETED = "managed_account.deleted"
    MANAGED_ACCOUNT_CODE_REISSUED = "managed_account.code_reissued"
    MANAGED_ACCOUNT_OPEN_AS = "managed_account.open_as"
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
    ORG_BALANCE_ADJUSTED = "org.balance_adjusted"
    ORG_BALANCE_CYCLE_DEBITED = "org.balance_cycle_debited"
    ORG_INVITATION_SENT = "org.invitation_sent"
    ORG_INVITATION_CANCELED = "org.invitation_canceled"
    ORG_INVITATION_ACCEPTED = "org.invitation_accepted"
    ORG_INVITATION_DECLINED = "org.invitation_declined"
    # Conversation/Support events
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_MESSAGE_SENT = "conversation.message_sent"
    CONVERSATION_ADMIN_REPLY = "conversation.admin_reply"
    CONVERSATION_CLOSED = "conversation.closed"
    CONVERSATION_REOPENED = "conversation.reopened"


# Metadata for event types (labels and categories for UI)
CORE_EVENT_TYPES = {
    EventType.USER_LOGIN: {"label": "User Login", "category": "auth"},
    EventType.USER_LOGIN_CODE: {"label": "User Login (access code)", "category": "auth"},
    EventType.USER_LOGIN_CODE_FAIL: {"label": "Access Code Login Failed", "category": "auth"},
    EventType.USER_LOGOUT: {"label": "User Logout", "category": "auth"},
    EventType.USER_REGISTER: {"label": "User Register", "category": "auth"},
    EventType.USER_PASSWORD_RESET_REQUEST: {"label": "Password Reset Request", "category": "auth"},
    EventType.USER_PASSWORD_RESET: {"label": "Password Reset", "category": "auth"},
    EventType.USER_EMAIL_VERIFY: {"label": "Email Verified", "category": "auth"},
    EventType.USER_PROFILE_UPDATE: {"label": "Profile Updated", "category": "user"},
    EventType.USER_PASSWORD_CHANGE: {"label": "Password Changed", "category": "user"},
    EventType.USER_DELETE_REQUEST: {"label": "Account Deletion Requested", "category": "user"},
    EventType.USER_DELETE_COMPLETE: {"label": "Account Deletion Completed", "category": "user"},
    EventType.ADMIN_IMPERSONATE_START: {"label": "Impersonation Started", "category": "admin"},
    EventType.ADMIN_IMPERSONATE_STOP: {"label": "Impersonation Stopped", "category": "admin"},
    EventType.ADMIN_USER_UPDATE: {"label": "User Updated by Admin", "category": "admin"},
    EventType.ADMIN_USER_DELETE: {"label": "User Deleted by Admin", "category": "admin"},
    EventType.MANAGED_GROUP_CREATED: {"label": "Managed Group Created", "category": "managed_account"},
    EventType.MANAGED_GROUP_UPDATED: {"label": "Managed Group Updated", "category": "managed_account"},
    EventType.MANAGED_GROUP_DELETED: {"label": "Managed Group Deleted", "category": "managed_account"},
    EventType.MANAGED_GROUP_TOKEN_ROTATED: {"label": "Managed Group Token Rotated", "category": "managed_account"},
    EventType.MANAGED_ACCOUNT_CREATED: {"label": "Managed Account Created", "category": "managed_account"},
    EventType.MANAGED_ACCOUNT_UPDATED: {"label": "Managed Account Updated", "category": "managed_account"},
    EventType.MANAGED_ACCOUNT_DELETED: {"label": "Managed Account Deleted", "category": "managed_account"},
    EventType.MANAGED_ACCOUNT_CODE_REISSUED: {"label": "Managed Account Code Reissued", "category": "managed_account"},
    EventType.MANAGED_ACCOUNT_OPEN_AS: {"label": "Open As Managed Account", "category": "managed_account"},
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
    EventType.ORG_BALANCE_ADJUSTED: {"label": "Organization Balance Adjusted", "category": "organization"},
    EventType.ORG_BALANCE_CYCLE_DEBITED: {"label": "Organization Cycle Debited", "category": "organization"},
    EventType.ORG_INVITATION_SENT: {"label": "Invitation Sent", "category": "organization"},
    EventType.ORG_INVITATION_CANCELED: {"label": "Invitation Canceled", "category": "organization"},
    EventType.ORG_INVITATION_ACCEPTED: {"label": "Invitation Accepted", "category": "organization"},
    EventType.ORG_INVITATION_DECLINED: {"label": "Invitation Declined", "category": "organization"},
    EventType.CONVERSATION_CREATED: {"label": "Support Conversation Created", "category": "conversation"},
    EventType.CONVERSATION_MESSAGE_SENT: {"label": "Support Message Sent", "category": "conversation"},
    EventType.CONVERSATION_ADMIN_REPLY: {"label": "Admin Reply Sent", "category": "conversation"},
    EventType.CONVERSATION_CLOSED: {"label": "Conversation Closed", "category": "conversation"},
    EventType.CONVERSATION_REOPENED: {"label": "Conversation Reopened", "category": "conversation"},
}


class CoreConversationSubtype(StrEnum):
    """User-initiable conversation subtypes that ship with the starterpack.

    Sub-apps widen the accepted set by overriding ``UserInitiableSubtype`` in ``constants_ext.py``.
    """

    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
