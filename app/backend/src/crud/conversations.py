# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CRUD operations for conversations and messages."""

from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.conversation import ConversationBase, ConversationParticipantBase, ConversationType, MessageBase


def _find_participant(
    session: Session,
    conversation_id: int,
    user_id: int,
) -> ConversationParticipantBase | None:
    return (
        session.query(ConversationParticipantBase)
        .filter(
            ConversationParticipantBase.conversation_id == conversation_id,
            ConversationParticipantBase.user_id == user_id,
        )
        .first()
    )


def add_participant(
    session: Session,
    conversation_id: int,
    user_id: int,
    last_read_at: datetime | None = None,
) -> ConversationParticipantBase:
    """Add a user as a participant to a conversation, or update if already exists."""
    participant = _find_participant(session, conversation_id, user_id)
    if participant:
        if last_read_at is not None:
            participant.last_read_at = last_read_at
        return participant

    participant = ConversationParticipantBase(
        conversation_id=conversation_id,
        user_id=user_id,
        last_read_at=last_read_at,
    )
    session.add(participant)
    return participant


def _create_conversation_with_initial_message(
    session: Session,
    *,
    creator_id: int,
    subject: str | None,
    subtype: str | None,
    initial_content: str,
    conversation_type: str,
    is_admin_response: bool,
) -> ConversationBase:
    """Create a conversation, its first message, and add the creator as a (read) participant."""
    conversation = ConversationBase(
        type=conversation_type,
        subject=subject,
        subtype=subtype,
        created_by_id=creator_id,
    )
    session.add(conversation)
    session.flush()

    session.add(MessageBase(
        conversation_id=conversation.id,
        sender_id=creator_id,
        content=initial_content,
        is_admin_response=is_admin_response,
    ))
    add_participant(session, conversation.id, creator_id, last_read_at=datetime.now(UTC))
    return conversation


def create_conversation(
    session: Session,
    user_id: int,
    subject: str | None,
    initial_content: str,
    conversation_type: str = ConversationType.SUPPORT.value,
    subtype: str | None = None,
) -> ConversationBase:
    conversation = _create_conversation_with_initial_message(
        session,
        creator_id=user_id,
        subject=subject,
        subtype=subtype,
        initial_content=initial_content,
        conversation_type=conversation_type,
        is_admin_response=False,
    )
    session.commit()
    session.refresh(conversation)
    return conversation


def create_admin_conversation(
    session: Session,
    admin_user_id: int,
    subject: str | None,
    initial_content: str,
    participant_user_ids: list[int],
    subtype: str | None = None,
) -> ConversationBase:
    """Create a conversation initiated by an admin with specific users as participants."""
    conversation = _create_conversation_with_initial_message(
        session,
        creator_id=admin_user_id,
        subject=subject,
        subtype=subtype,
        initial_content=initial_content,
        conversation_type=ConversationType.SUPPORT.value,
        is_admin_response=True,
    )
    # Target users join unread; admin is already a (read) participant.
    for user_id in participant_user_ids:
        if user_id != admin_user_id:
            add_participant(session, conversation.id, user_id)
    session.commit()
    session.refresh(conversation)
    return conversation


def get_conversation_by_id(session: Session, conversation_id: int) -> ConversationBase | None:
    """Get a conversation by ID."""
    return session.query(ConversationBase).filter(ConversationBase.id == conversation_id).first()


def get_user_conversations(
    session: Session,
    user_id: int,
    include_closed: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ConversationBase], int]:
    """Get conversations where the user is the creator or a participant."""
    participant_conv_ids = (
        session.query(ConversationParticipantBase.conversation_id)
        .filter(ConversationParticipantBase.user_id == user_id)
        .subquery()
    )
    query = session.query(ConversationBase).filter(
        (ConversationBase.created_by_id == user_id) | (ConversationBase.id.in_(participant_conv_ids))
    )

    if not include_closed:
        query = query.filter(ConversationBase.is_closed == False)  # noqa: E712

    total = query.count()
    conversations = query.order_by(ConversationBase.updated_at.desc()).offset(offset).limit(limit).all()

    return conversations, total


def get_all_support_conversations(
    session: Session,
    include_closed: bool = False,
    limit: int = 50,
    offset: int = 0,
    subtype: str | None = None,
) -> tuple[list[ConversationBase], int]:
    """Get all support conversations (for admin)."""
    query = session.query(ConversationBase).filter(ConversationBase.type == ConversationType.SUPPORT.value)

    if not include_closed:
        query = query.filter(ConversationBase.is_closed == False)  # noqa: E712

    if subtype is not None:
        query = query.filter(ConversationBase.subtype == subtype)

    total = query.count()
    conversations = query.order_by(ConversationBase.updated_at.desc()).offset(offset).limit(limit).all()

    return conversations, total


def add_message(
    session: Session,
    conversation_id: int,
    sender_id: int,
    content: str,
    is_admin_response: bool = False,
) -> MessageBase:
    """Add a message to a conversation."""
    message = MessageBase(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        is_admin_response=is_admin_response,
    )
    session.add(message)

    # Update conversation's updated_at timestamp
    conversation = get_conversation_by_id(session, conversation_id)
    if conversation:
        conversation.updated_at = datetime.now(UTC)

    session.commit()
    session.refresh(message)
    return message


def get_messages(
    session: Session,
    conversation_id: int,
    limit: int = 50,
    offset: int = 0,
    before_id: int | None = None,
) -> tuple[list[MessageBase], int, bool]:
    """Get messages for a conversation with pagination."""
    query = session.query(MessageBase).filter(MessageBase.conversation_id == conversation_id)

    if before_id:
        query = query.filter(MessageBase.id < before_id)

    total = query.count()
    messages = query.order_by(MessageBase.created_at.desc()).offset(offset).limit(limit + 1).all()

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Reverse to get chronological order
    messages.reverse()

    return messages, total, has_more


def get_last_message(session: Session, conversation_id: int) -> MessageBase | None:
    """Get the last message in a conversation."""
    return (
        session.query(MessageBase)
        .filter(MessageBase.conversation_id == conversation_id)
        .order_by(MessageBase.created_at.desc())
        .first()
    )


def get_last_messages_for(
    session: Session, conversation_ids: list[int]
) -> dict[int, MessageBase]:
    """Return ``{conversation_id: last_message}`` in a single query.

    Uses Postgres DISTINCT ON to pick the newest message per conversation —
    avoids N round-trips when rendering a conversation list.
    """
    if not conversation_ids:
        return {}
    rows = (
        session.query(MessageBase)
        .filter(MessageBase.conversation_id.in_(conversation_ids))
        .order_by(MessageBase.conversation_id, MessageBase.created_at.desc())
        .distinct(MessageBase.conversation_id)
        .all()
    )
    return {m.conversation_id: m for m in rows}


def mark_as_read(session: Session, conversation_id: int, user_id: int) -> None:
    """Mark a conversation as read for a user."""
    add_participant(session, conversation_id, user_id, last_read_at=datetime.now(UTC))
    session.commit()


def get_unread_count(session: Session, conversation_id: int, user_id: int) -> int:
    """Get the count of unread messages for a user in a conversation."""
    participant = _find_participant(session, conversation_id, user_id)
    last_read_at = participant.last_read_at if participant else None

    query = session.query(func.count(MessageBase.id)).filter(
        MessageBase.conversation_id == conversation_id,
        MessageBase.sender_id != user_id,
    )
    if last_read_at is not None:
        query = query.filter(MessageBase.created_at > last_read_at)
    return query.scalar() or 0


def get_unread_counts_for(
    session: Session, pairs: list[tuple[int, int]]
) -> dict[tuple[int, int], int]:
    """Return ``{(conversation_id, user_id): unread_count}`` in 1 + N queries.

    One batched query fetches participants (for last_read_at), then one COUNT
    per pair. Net cost is 1 + N instead of the per-call 2N from get_unread_count;
    a single GROUP BY would be 1 query total but each pair has a different
    last_read_at cutoff, which doesn't fold cleanly into one aggregate.
    """
    if not pairs:
        return {}

    participants = (
        session.query(ConversationParticipantBase)
        .filter(
            ConversationParticipantBase.conversation_id.in_({p[0] for p in pairs}),
            ConversationParticipantBase.user_id.in_({p[1] for p in pairs}),
        )
        .all()
    )
    last_read_map: dict[tuple[int, int], datetime | None] = {
        (p.conversation_id, p.user_id): p.last_read_at for p in participants
    }

    counts: dict[tuple[int, int], int] = {}
    for conv_id, user_id in pairs:
        last_read_at = last_read_map.get((conv_id, user_id))
        q = session.query(func.count(MessageBase.id)).filter(
            MessageBase.conversation_id == conv_id,
            MessageBase.sender_id != user_id,
        )
        if last_read_at is not None:
            q = q.filter(MessageBase.created_at > last_read_at)
        counts[(conv_id, user_id)] = q.scalar() or 0
    return counts


def _set_closed(session: Session, conversation_id: int, *, closed: bool) -> ConversationBase | None:
    conversation = get_conversation_by_id(session, conversation_id)
    if conversation:
        conversation.is_closed = closed
        conversation.closed_at = datetime.now(UTC) if closed else None
        session.commit()
        session.refresh(conversation)
    return conversation


def close_conversation(session: Session, conversation_id: int) -> ConversationBase | None:
    return _set_closed(session, conversation_id, closed=True)


def reopen_conversation(session: Session, conversation_id: int) -> ConversationBase | None:
    return _set_closed(session, conversation_id, closed=False)


def user_can_access_conversation(session: Session, conversation_id: int, user_id: int) -> bool:
    """Check if a user can access a conversation (as creator or participant)."""
    conversation = get_conversation_by_id(session, conversation_id)
    if not conversation:
        return False

    if conversation.created_by_id == user_id:
        return True

    return _find_participant(session, conversation_id, user_id) is not None
