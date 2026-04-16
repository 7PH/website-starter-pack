# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CRUD operations for conversations and messages."""

from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.conversation import ConversationBase, ConversationParticipantBase, ConversationType, MessageBase


def add_participant(
    session: Session,
    conversation_id: int,
    user_id: int,
    last_read_at: datetime | None = None,
) -> ConversationParticipantBase:
    """Add a user as a participant to a conversation, or update if already exists."""
    participant = (
        session.query(ConversationParticipantBase)
        .filter(
            ConversationParticipantBase.conversation_id == conversation_id,
            ConversationParticipantBase.user_id == user_id,
        )
        .first()
    )
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


def create_conversation(
    session: Session,
    user_id: int,
    subject: str | None,
    initial_content: str,
    conversation_type: str = ConversationType.SUPPORT.value,
    subtype: str | None = None,
) -> ConversationBase:
    """Create a new conversation with an initial message."""
    conversation = ConversationBase(
        type=conversation_type,
        subject=subject,
        subtype=subtype,
        created_by_id=user_id,
    )
    session.add(conversation)
    session.flush()

    message = MessageBase(
        conversation_id=conversation.id,
        sender_id=user_id,
        content=initial_content,
        is_admin_response=False,
    )
    session.add(message)

    add_participant(session, conversation.id, user_id, last_read_at=datetime.now(UTC))

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
    conversation = ConversationBase(
        type=ConversationType.SUPPORT.value,
        subject=subject,
        subtype=subtype,
        created_by_id=admin_user_id,
    )
    session.add(conversation)
    session.flush()

    message = MessageBase(
        conversation_id=conversation.id,
        sender_id=admin_user_id,
        content=initial_content,
        is_admin_response=True,
    )
    session.add(message)

    # Add admin as participant (already read)
    add_participant(session, conversation.id, admin_user_id, last_read_at=datetime.now(UTC))

    # Add target users as participants (unread), skipping admin (already added above)
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


def mark_as_read(session: Session, conversation_id: int, user_id: int) -> None:
    """Mark a conversation as read for a user."""
    add_participant(session, conversation_id, user_id, last_read_at=datetime.now(UTC))
    session.commit()


def get_unread_count(session: Session, conversation_id: int, user_id: int) -> int:
    """Get the count of unread messages for a user in a conversation."""
    participant = (
        session.query(ConversationParticipantBase)
        .filter(
            ConversationParticipantBase.conversation_id == conversation_id,
            ConversationParticipantBase.user_id == user_id,
        )
        .first()
    )

    if not participant or not participant.last_read_at:
        # If no read record, count all messages not from this user
        return (
            session.query(func.count(MessageBase.id))
            .filter(
                MessageBase.conversation_id == conversation_id,
                MessageBase.sender_id != user_id,
            )
            .scalar()
            or 0
        )

    # Count messages after last_read_at not from this user
    return (
        session.query(func.count(MessageBase.id))
        .filter(
            MessageBase.conversation_id == conversation_id,
            MessageBase.sender_id != user_id,
            MessageBase.created_at > participant.last_read_at,
        )
        .scalar()
        or 0
    )


def close_conversation(session: Session, conversation_id: int) -> ConversationBase | None:
    """Close a conversation."""
    conversation = get_conversation_by_id(session, conversation_id)
    if conversation:
        conversation.is_closed = True
        conversation.closed_at = datetime.now(UTC)
        session.commit()
        session.refresh(conversation)
    return conversation


def reopen_conversation(session: Session, conversation_id: int) -> ConversationBase | None:
    """Reopen a closed conversation."""
    conversation = get_conversation_by_id(session, conversation_id)
    if conversation:
        conversation.is_closed = False
        conversation.closed_at = None
        session.commit()
        session.refresh(conversation)
    return conversation


def user_can_access_conversation(session: Session, conversation_id: int, user_id: int) -> bool:
    """Check if a user can access a conversation (as creator or participant)."""
    conversation = get_conversation_by_id(session, conversation_id)
    if not conversation:
        return False

    if conversation.created_by_id == user_id:
        return True

    participant = (
        session.query(ConversationParticipantBase)
        .filter(
            ConversationParticipantBase.conversation_id == conversation_id,
            ConversationParticipantBase.user_id == user_id,
        )
        .first()
    )
    return participant is not None
