# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Conversations controller for support messaging system.
Handles user conversations and admin support management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..constants import CoreConversationSubtype, EventType
from ..crud.conversations import (
    add_message,
    close_conversation,
    create_admin_conversation,
    create_conversation,
    get_all_support_conversations,
    get_conversation_by_id,
    get_last_message,
    get_messages,
    get_unread_count,
    get_user_conversations,
    mark_as_read,
    reopen_conversation,
    user_can_access_conversation,
)
from ..crud.event_logs import log_event
from ..crud.users import get_user_by_id
from ..helpers.account import assert_min_account_age
from ..helpers.auth import get_current_admin, get_current_nonmanaged_user, get_current_user
from ..helpers.bug_report import strip_url_query_in_body
from ..helpers.db import get_session
from ..helpers.ratelimit import ensure_rate_limit
from ..models.conversation import ConversationBase, MessageBase
from ..schemas.conversation import (
    AdminConversationCreate,
    ConversationCreate,
    ConversationDetail,
    ConversationListResponse,
    ConversationRead,
    ConversationUpdate,
    ConversationUserPreview,
    MessageCreate,
    MessageListResponse,
    MessageRead,
)
from ..schemas.user import UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations")
admin_router = APIRouter(prefix="/admin/conversations")

# Rate limits
CONVERSATION_CREATE_HOURLY_QUOTA = 5  # Max new conversations per (user, subtype) per hour
CONVERSATION_CREATE_HOURLY_DURATION = 60  # 1 hour
CONVERSATION_CREATE_DAILY_QUOTA = 20  # Max new conversations per (user, subtype) per day
CONVERSATION_CREATE_DAILY_DURATION = 60 * 24  # 24 hours
MIN_ACCOUNT_AGE_MINUTES = 10  # Reject conversations from accounts younger than this
MESSAGE_SEND_RATE_LIMIT = 30  # Max messages per minute
MESSAGE_SEND_RATE_LIMIT_DURATION = 1  # 1 minute


# ============================================================================
# Helpers
# ============================================================================


def _user_preview(user) -> ConversationUserPreview | None:
    if not user:
        return None
    return ConversationUserPreview(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )


def _get_conversation_or_404(session: Session, conversation_id: int) -> ConversationBase:
    conv = get_conversation_by_id(session, conversation_id)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


def _get_user_conversation_or_404(session: Session, conversation_id: int, user_id: int) -> ConversationBase:
    """Return the conversation if the user can access it, else 404.

    Hides existence of conversations from unauthorized users (no 403).
    """
    if not user_can_access_conversation(session, conversation_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return _get_conversation_or_404(session, conversation_id)


def _message_to_read(message: MessageBase) -> MessageRead:
    return MessageRead(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        sender=_user_preview(message.sender),
        content=message.content,
        is_admin_response=message.is_admin_response,
        created_at=message.created_at,
    )


def _conversation_base_fields(conversation: ConversationBase, unread_count: int = 0) -> dict:
    return dict(
        id=conversation.id,
        type=conversation.type,
        subtype=conversation.subtype,
        subject=conversation.subject,
        created_by_id=conversation.created_by_id,
        created_by=_user_preview(conversation.created_by),
        is_closed=conversation.is_closed,
        closed_at=conversation.closed_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        unread_count=unread_count,
    )


def _conversation_to_read(
    conversation: ConversationBase,
    unread_count: int = 0,
    last_message: MessageBase | None = None,
) -> ConversationRead:
    return ConversationRead(
        **_conversation_base_fields(conversation, unread_count),
        last_message=_message_to_read(last_message) if last_message else None,
    )


def _build_list_response(
    session: Session,
    conversations: list[ConversationBase],
    total: int,
    limit: int,
    offset: int,
    *,
    unread_for_user_id: int | None,
) -> "ConversationListResponse":
    """Build a paginated conversation list, attaching unread count + last message per row.

    ``unread_for_user_id`` controls whose perspective the unread count is from
    (use the conversation creator for the admin list, the current user for the
    user list).
    """
    items = []
    for conv in conversations:
        target_user = unread_for_user_id if unread_for_user_id is not None else conv.created_by_id
        unread = get_unread_count(session, conv.id, target_user) if target_user is not None else 0
        last_msg = get_last_message(session, conv.id)
        items.append(_conversation_to_read(conv, unread_count=unread, last_message=last_msg))
    return ConversationListResponse(items=items, total=total, limit=limit, offset=offset)


def _conversation_to_detail(
    conversation: ConversationBase,
    messages: list[MessageBase],
    unread_count: int = 0,
) -> ConversationDetail:
    return ConversationDetail(
        **_conversation_base_fields(conversation, unread_count),
        messages=[_message_to_read(m) for m in messages],
    )


# ============================================================================
# User Endpoints
# ============================================================================


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_new_conversation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    # Managed accounts can't open support conversations; their owner does.
    user: UserRead = Depends(get_current_nonmanaged_user),
    data: ConversationCreate,
):
    """Create a new support conversation."""
    assert_min_account_age(session, user.id, min_minutes=MIN_ACCOUNT_AGE_MINUTES)

    # Independent rate-limit counters per subtype so a bug-report burst doesn't
    # lock out legitimate support use (and vice versa).
    rate_limit_action = f"conversation-create:{data.subtype or 'default'}"
    ensure_rate_limit(
        action=rate_limit_action,
        quota=CONVERSATION_CREATE_HOURLY_QUOTA,
        key=str(user.id),
        duration_minutes=CONVERSATION_CREATE_HOURLY_DURATION,
    )
    ensure_rate_limit(
        action=rate_limit_action,
        quota=CONVERSATION_CREATE_DAILY_QUOTA,
        key=str(user.id),
        duration_minutes=CONVERSATION_CREATE_DAILY_DURATION,
    )

    if data.subtype == CoreConversationSubtype.BUG_REPORT:
        # Defense in depth: strip query strings/fragments the client may have
        # missed. Tokens in those are the whole point of doing it here too.
        data.content = strip_url_query_in_body(data.content)

    conversation = create_conversation(
        session=session,
        user_id=user.id,
        subject=data.subject,
        initial_content=data.content,
        subtype=data.subtype,
    )

    log_event(
        session,
        action=EventType.CONVERSATION_CREATED,
        user_id=user.id,
        details={
            "conversation_id": conversation.id,
            "subject": data.subject,
            "subtype": data.subtype,
        },
        request=request,
    )

    return _conversation_to_read(conversation, unread_count=0)


@router.get("", response_model=ConversationListResponse)
def list_user_conversations(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    include_closed: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List current user's conversations."""
    conversations, total = get_user_conversations(
        session=session,
        user_id=user.id,
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )
    return _build_list_response(session, conversations, total, limit, offset, unread_for_user_id=user.id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_user_conversation(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    conversation_id: int,
):
    """Get a conversation by ID with messages."""
    conversation = _get_user_conversation_or_404(session, conversation_id, user.id)

    messages, _, _ = get_messages(session, conversation_id, limit=100)
    unread = get_unread_count(session, conversation_id, user.id)

    # Mark as read when viewing
    mark_as_read(session, conversation_id, user.id)

    return _conversation_to_detail(conversation, messages, unread_count=unread)


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
def get_conversation_messages(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    before_id: int | None = Query(None),
):
    """Get paginated messages for a conversation."""
    _get_user_conversation_or_404(session, conversation_id, user.id)

    messages, total, has_more = get_messages(
        session=session,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
        before_id=before_id,
    )

    return MessageListResponse(
        items=[_message_to_read(m) for m in messages],
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )


@router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def send_message(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_nonmanaged_user),
    conversation_id: int,
    data: MessageCreate,
):
    """Send a message in a conversation."""
    # Rate limit: max messages per minute per user
    ensure_rate_limit(
        action="message-send",
        quota=MESSAGE_SEND_RATE_LIMIT,
        key=str(user.id),
        duration_minutes=MESSAGE_SEND_RATE_LIMIT_DURATION,
    )

    conversation = _get_user_conversation_or_404(session, conversation_id, user.id)

    if conversation.is_closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send messages to a closed conversation",
        )

    message = add_message(
        session=session,
        conversation_id=conversation_id,
        sender_id=user.id,
        content=data.content,
        is_admin_response=False,
    )

    log_event(
        session,
        action=EventType.CONVERSATION_MESSAGE_SENT,
        user_id=user.id,
        details={"conversation_id": conversation_id, "message_id": message.id},
        request=request,
    )

    return _message_to_read(message)


# ============================================================================
# Admin Endpoints
# ============================================================================


@admin_router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def admin_create_conversation(
    *,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
    data: AdminConversationCreate,
):
    """Create a conversation with specific users as participants (admin only)."""
    # Validate all participant users exist
    for user_id in data.participant_user_ids:
        user = get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user_id} not found",
            )

    conversation = create_admin_conversation(
        session=session,
        admin_user_id=admin.id,
        subject=data.subject,
        initial_content=data.content,
        participant_user_ids=data.participant_user_ids,
        subtype=data.subtype,
    )

    log_event(
        session=session,
        user_id=admin.id,
        action=EventType.CONVERSATION_CREATED,
        details={"conversation_id": conversation.id, "participant_user_ids": data.participant_user_ids},
    )

    return _conversation_to_read(conversation)


@admin_router.get("", response_model=ConversationListResponse)
def admin_list_conversations(
    *,
    session: Session = Depends(get_session),
    _admin: UserRead = Depends(get_current_admin),
    include_closed: bool = Query(False),
    subtype: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all support conversations (admin only)."""
    conversations, total = get_all_support_conversations(
        session=session,
        include_closed=include_closed,
        subtype=subtype,
        limit=limit,
        offset=offset,
    )
    # Admin view: show unread from the conversation creator's perspective.
    return _build_list_response(session, conversations, total, limit, offset, unread_for_user_id=None)


@admin_router.get("/{conversation_id}", response_model=ConversationDetail)
def admin_get_conversation(
    *,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
    conversation_id: int,
):
    """Get any conversation by ID (admin only)."""
    conversation = _get_conversation_or_404(session, conversation_id)

    messages, _, _ = get_messages(session, conversation_id, limit=100)

    # Mark as read for admin
    mark_as_read(session, conversation_id, admin.id)

    return _conversation_to_detail(conversation, messages, unread_count=0)


@admin_router.patch("/{conversation_id}", response_model=ConversationRead)
def admin_update_conversation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    conversation_id: int,
    data: ConversationUpdate,
):
    """Update a conversation (admin only). Used to close/reopen conversations."""
    conversation = _get_conversation_or_404(session, conversation_id)

    # Handle is_closed update
    if data.is_closed is not None:
        if data.is_closed and not conversation.is_closed:
            # Close the conversation
            conversation = close_conversation(session, conversation_id)
            log_event(
                session,
                action=EventType.CONVERSATION_CLOSED,
                user_id=admin.id,
                details={"conversation_id": conversation_id},
                request=request,
            )
        elif not data.is_closed and conversation.is_closed:
            # Reopen the conversation
            conversation = reopen_conversation(session, conversation_id)
            log_event(
                session,
                action=EventType.CONVERSATION_REOPENED,
                user_id=admin.id,
                details={"conversation_id": conversation_id},
                request=request,
            )

    return _conversation_to_read(conversation, unread_count=0)


@admin_router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def admin_send_message(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    conversation_id: int,
    data: MessageCreate,
):
    """Send an admin reply to a conversation."""
    conversation = _get_conversation_or_404(session, conversation_id)

    if conversation.is_closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send messages to a closed conversation",
        )

    message = add_message(
        session=session,
        conversation_id=conversation_id,
        sender_id=admin.id,
        content=data.content,
        is_admin_response=True,
    )

    log_event(
        session,
        action=EventType.CONVERSATION_ADMIN_REPLY,
        user_id=admin.id,
        details={"conversation_id": conversation_id, "message_id": message.id},
        request=request,
    )

    # TODO: Send email notification to user about admin reply

    return _message_to_read(message)
