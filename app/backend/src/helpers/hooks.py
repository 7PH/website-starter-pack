# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Typed event-bus for pluggable starterpack hooks.

Sub-apps register handlers from ``main_ext.py`` with ``@on(EventClass)``.
The starterpack fires events with ``fire(session, event)``. Handlers run
in registration order; later handlers see earlier mutations.

Conventions:
- Handlers have signature ``(session: Session, event: E) -> None``.
- Single-result events expose a named mutable field (``allow``, ``valid``,
  ``user``, ``extra``). Handlers mutate it; the firing site reads it back.
- Gate events that may want to surface a human-readable failure message
  pair ``allow: bool`` with ``reason: str | None`` — handlers set both
  together, the firing site uses ``reason`` in the error response.
- Multi-handler events (e.g. SubscriptionChanged) have no mutation field;
  handlers observe and write to ``session``.
- No return values. No string keys. Handlers are identified by their
  module + qualname when needed for logging.

Discoverability: every hookable point is a ``HookEvent`` subclass defined
below. ``Find Usages`` of ``HookEvent`` lists them all; IDE go-to-definition
on an event class shows its schema and where it fires.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from fastapi import Request
    from sqlalchemy.orm import Session

    from ..models.organization import OrganizationBase
    from ..models.user import UserBase
    from ..schemas.user import UserRead

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base + registry
# ---------------------------------------------------------------------------


@dataclass
class HookEvent:
    """Base class for all starterpack hook events."""


type Handler = Callable[["Session", Any], None]

_registry: dict[type, list[Handler]] = defaultdict(list)


def on[E: HookEvent](event_type: type[E]) -> Callable[[Callable[[Session, E], None]], Callable[[Session, E], None]]:
    """Register a handler for ``event_type``.

    Use as a decorator from ``main_ext.py`` (or any module imported at
    startup). Multiple handlers can register for the same event type.
    """

    def decorator(fn: Callable[[Session, E], None]) -> Callable[[Session, E], None]:
        _registry[event_type].append(fn)
        return fn

    return decorator


def has_handlers(event_type: type[HookEvent]) -> bool:
    """Whether at least one handler is registered for ``event_type``.

    Useful for endpoints that want to behave as ``404 Not Found`` when no
    app has opted in (instead of running with a no-op event).
    """
    return bool(_registry.get(event_type))


def fire[E: HookEvent](session: Session, event: E) -> E:
    """Run every registered handler for ``type(event)`` and return the event.

    Errors raised by a handler are logged and swallowed — one bad app
    handler must not break the request. The starterpack's own writes
    happen *before* fire() is called, so a handler failure can't roll
    them back.
    """
    for fn in _registry.get(type(event), []):
        try:
            fn(session, event)
        except Exception:
            logger.exception(
                "Hook handler %s:%s failed on %s",
                getattr(fn, "__module__", "?"),
                getattr(fn, "__qualname__", "?"),
                type(event).__name__,
            )
    return event


def _reset_hooks_for_tests() -> None:
    """Test-only helper. Do not call from production code."""
    _registry.clear()


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------


@dataclass
class SubscriptionChanged(HookEvent):
    """Stripe ``customer.subscription.*`` webhook event.

    Fired AFTER the starterpack's own user/org premium update, in the same
    request-scoped session so app-side writes commit atomically with it.

    Idempotency: Stripe may deliver the same event more than once. Make
    handlers idempotent in shape (``ON CONFLICT DO NOTHING``,
    ``UPDATE ... WHERE``, etc.). The starterpack does not dedupe events.

    ``user`` and ``organization`` are resolved by the starterpack from the
    Stripe customer ID; exactly one is set, or both are None if the customer
    isn't linked to anything we know about.
    """

    action: Literal["created", "updated", "deleted"]
    raw_event: dict
    user: UserBase | None = None
    organization: OrganizationBase | None = None


@dataclass
class GroupManagementCheck(HookEvent):
    """Fired before any managed-account-group OR managed-account write.

    Default ``allow=True``. Handlers set ``event.allow = False`` to deny.
    Managed accounts are denied earlier in the dependency, before this
    event fires — handlers don't need to special-case them.
    """

    user: UserRead
    allow: bool = True


@dataclass
class ManagedAccountSeatGate(HookEvent):
    """Fired before a managed-account create (single or bulk).

    Default ``allow=True``. Handlers set ``allow=False`` to deny — typically
    because the user's tier-specific seat quota would be exceeded. The
    starterpack-level ``MANAGED_ACCOUNTS_MAX_PER_USER`` env cap still runs
    independently as a baseline guardrail; this hook layers per-tier rules
    on top.

    Set ``reason`` to surface a human-readable message in the 402 response
    body. Leave ``None`` for a generic "Seat quota exceeded" string.

    ``count_to_create`` is the worst-case number of new accounts the request
    would create (1 for the single-create endpoint, ``len(payload)`` for
    bulk — handlers see the upper bound, mirroring the env-cap check).
    """

    user: UserRead
    group_id: int
    count_to_create: int
    allow: bool = True
    reason: str | None = None


@dataclass
class AccessCodeResolution(HookEvent):
    """Fired by ``POST /auth/code`` to resolve a (managed_account_id, code) pair.

    Handlers set ``event.user`` to the resolved ``UserBase`` if the code is
    valid, or leave it as None to reject. The first handler to set
    ``event.user`` wins; subsequent handlers should short-circuit on a
    non-None value to allow chaining.

    If no handler sets ``event.user``, the endpoint returns 404 (acts as
    if the route isn't configured).
    """

    managed_account_id: int
    code: str
    request: Request
    user: UserBase | None = None


@dataclass
class UserReadAssembled(HookEvent):
    """Fired after the starterpack assembles a ``UserRead``.

    Handlers append app-side fields to ``event.extra``. The dict is merged
    into the ``UserRead.extra`` field of the outgoing response. Use this
    for tier metadata, feature flags, seat quotas, etc. — anything the
    frontend needs without a separate round-trip.

    The same event fires when minting JWTs (so ``auth.user.extra`` is
    populated on login/refresh) and when serving ``GET /users/me``.
    """

    user: UserRead
    extra: dict[str, Any] = field(default_factory=dict)
