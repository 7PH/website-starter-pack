# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CRUD operations for organizations."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..models.organization import OrganizationBase, UserOrganizationBase

# Organization CRUD


def get_organization_by_id(
    session: Session, org_id: int, include_deleted: bool = False
) -> OrganizationBase | None:
    """Retrieve an organization by ID. By default excludes deleted orgs."""
    org = session.get(OrganizationBase, org_id)
    if org and not include_deleted and org.deleted_at is not None:
        return None
    return org


def get_organization_by_email(session: Session, email: str) -> OrganizationBase | None:
    """Retrieve a non-deleted organization by email."""
    return session.execute(
        select(OrganizationBase).where(
            OrganizationBase.email == email, OrganizationBase.deleted_at.is_(None)
        )
    ).scalar_one_or_none()


def get_organization_by_stripe_id(session: Session, stripe_id: str) -> OrganizationBase | None:
    """Retrieve a non-deleted organization by Stripe customer ID."""
    return session.execute(
        select(OrganizationBase).where(
            OrganizationBase.stripe_id == stripe_id, OrganizationBase.deleted_at.is_(None)
        )
    ).scalar_one_or_none()


def get_organizations(
    session: Session,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    include_deleted: bool = False,
) -> tuple[list[OrganizationBase], int]:
    """Get paginated list of organizations with total count."""
    query = select(OrganizationBase)
    if not include_deleted:
        query = query.where(OrganizationBase.deleted_at.is_(None))

    # Apply search filter at SQL level
    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.where(
            func.lower(OrganizationBase.name).like(search_pattern)
            | func.lower(OrganizationBase.email).like(search_pattern)
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.execute(count_query).scalar() or 0

    # Get paginated results
    query = query.order_by(OrganizationBase.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    orgs = list(session.execute(query).scalars().all())

    return orgs, total


def get_org_member_counts(session: Session, org_ids: list[int]) -> dict[int, tuple[int, int]]:
    """Return {org_id: (member_count, premium_count)} for the given orgs."""
    if not org_ids:
        return {}

    rows = session.execute(
        select(
            UserOrganizationBase.organization_id,
            func.count().label("members"),
            func.count().filter(UserOrganizationBase.has_premium_seat.is_(True)).label("premium"),
        )
        .where(UserOrganizationBase.organization_id.in_(org_ids))
        .group_by(UserOrganizationBase.organization_id)
    ).all()
    counts = {org_id: (members, premium) for org_id, members, premium in rows}
    return {org_id: counts.get(org_id, (0, 0)) for org_id in org_ids}


def create_organization(session: Session, org: OrganizationBase) -> OrganizationBase:
    """Add a new organization to the database."""
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def update_organization(session: Session, org: OrganizationBase) -> None:
    """Commit changes to an existing organization."""
    session.commit()


def soft_delete_organization(session: Session, org: OrganizationBase) -> None:
    """Soft delete an organization."""
    org.deleted_at = datetime.now(UTC)
    session.commit()


def is_org_email_taken(session: Session, email: str, exclude_org_id: int | None = None) -> bool:
    """Check if an email is already used by a non-deleted organization."""
    query = select(OrganizationBase).where(
        OrganizationBase.email == email, OrganizationBase.deleted_at.is_(None)
    )
    if exclude_org_id:
        query = query.where(OrganizationBase.id != exclude_org_id)
    return session.execute(query).scalar_one_or_none() is not None


# User-Organization Membership CRUD


def get_user_org_membership(
    session: Session, user_id: int, org_id: int
) -> UserOrganizationBase | None:
    """Get a user's membership in a specific organization."""
    return session.get(UserOrganizationBase, (user_id, org_id))


def get_user_organizations(session: Session, user_id: int) -> list[UserOrganizationBase]:
    """Get all organization memberships for a user."""
    return list(
        session.execute(
            select(UserOrganizationBase)
            .where(UserOrganizationBase.user_id == user_id)
            .options(joinedload(UserOrganizationBase.organization))
        )
        .scalars()
        .all()
    )


def get_organization_members(
    session: Session,
    org_id: int,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[UserOrganizationBase], int]:
    """Get paginated list of organization members with total count."""
    query = (
        select(UserOrganizationBase)
        .where(UserOrganizationBase.organization_id == org_id)
        .options(joinedload(UserOrganizationBase.user))
    )

    # Get total count
    count_query = select(func.count()).select_from(
        select(UserOrganizationBase).where(UserOrganizationBase.organization_id == org_id).subquery()
    )
    total = session.execute(count_query).scalar() or 0

    # Get paginated results
    query = query.order_by(UserOrganizationBase.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    members = list(session.execute(query).scalars().all())

    return members, total


def add_organization_member(
    session: Session, user_id: int, org_id: int, is_admin: bool = False
) -> UserOrganizationBase:
    """Add a user as a member of an organization."""
    membership = UserOrganizationBase(
        user_id=user_id,
        organization_id=org_id,
        is_admin=is_admin,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def remove_organization_member(session: Session, membership: UserOrganizationBase) -> None:
    """Remove a user from an organization."""
    session.delete(membership)
    session.commit()


def update_organization_member(session: Session, membership: UserOrganizationBase) -> None:
    """Commit changes to a membership."""
    session.commit()


def is_org_admin(session: Session, user_id: int, org_id: int) -> bool:
    """Check if a user is an admin of a specific organization."""
    membership = get_user_org_membership(session, user_id, org_id)
    return membership is not None and membership.is_admin


def _count_memberships(session: Session, *filters) -> int:
    return session.execute(select(func.count()).where(*filters)).scalar() or 0


def count_org_admins(session: Session, org_id: int) -> int:
    return _count_memberships(
        session,
        UserOrganizationBase.organization_id == org_id,
        UserOrganizationBase.is_admin.is_(True),
    )


def count_org_premium_members(session: Session, org_id: int) -> int:
    return _count_memberships(
        session,
        UserOrganizationBase.organization_id == org_id,
        UserOrganizationBase.has_premium_seat.is_(True),
    )


def count_user_organizations(session: Session, user_id: int) -> int:
    return _count_memberships(session, UserOrganizationBase.user_id == user_id)


def count_organization_members(session: Session, org_id: int) -> int:
    return _count_memberships(session, UserOrganizationBase.organization_id == org_id)


def get_orgs_due_for_cycle_debit(session: Session, now: datetime) -> list[OrganizationBase]:
    """Return non-deleted orgs with an assigned plan whose cycle has ended."""
    return list(
        session.execute(
            select(OrganizationBase).where(
                OrganizationBase.deleted_at.is_(None),
                OrganizationBase.billing_price_id.is_not(None),
                OrganizationBase.billing_cycle_end.is_not(None),
                OrganizationBase.billing_cycle_end <= now,
            )
        ).scalars().all()
    )


def reset_org_members_premium(session: Session, org_id: int) -> list[int]:
    """Reset premium seats for all members of an organization.

    Returns list of affected user IDs so caller can update their premium cache.
    """
    members = session.execute(
        select(UserOrganizationBase)
        .where(
            UserOrganizationBase.organization_id == org_id,
            UserOrganizationBase.has_premium_seat.is_(True),
        )
    ).scalars().all()

    affected_user_ids = []
    for membership in members:
        membership.has_premium_seat = False
        affected_user_ids.append(membership.user_id)

    session.commit()
    return affected_user_ids
