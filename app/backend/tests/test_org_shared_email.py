# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Several organizations may share an email, eg two orgs created by the same user."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.controllers import organizations
from src.models.organization import OrganizationBase
from src.schemas.organization import OrganizationCreate, OrganizationUpdate

USER = SimpleNamespace(id=1, is_admin=False)
EMAIL = "owner@example.com"


def test_email_column_is_not_unique():
    """create_all would otherwise build the unique constraint on fresh installs."""
    assert not OrganizationBase.__table__.c.email.unique


def test_user_creates_two_orgs_with_the_same_email():
    with (
        patch.object(organizations, "ORG_SELF_SERVICE_CREATION", True),
        patch.object(organizations, "ORG_MAX_PER_USER", 5),
        patch.object(organizations, "count_user_organizations", return_value=0),
        patch.object(organizations, "create_organization", side_effect=lambda _s, org: org) as create,
        patch.object(organizations, "add_organization_member"),
        patch.object(organizations, "log_event"),
        patch.object(organizations, "_org_to_read", side_effect=lambda _s, org, _u: org),
    ):
        for name in ("First", "Second"):
            organizations.create_new_organization(
                session=MagicMock(), request=MagicMock(), user=USER, org_data=OrganizationCreate(name=name, email=EMAIL)
            )

    assert [c.args[1].email for c in create.call_args_list] == [EMAIL, EMAIL]


def test_update_to_another_orgs_email():
    org = OrganizationBase(id=2, name="Second", email="second@example.com", custom_data={})
    with (
        patch.object(organizations, "_check_org_access", return_value=org),
        patch.object(organizations, "update_organization") as update,
        patch.object(organizations, "log_event"),
        patch.object(organizations, "_org_to_read", side_effect=lambda _s, org, _u: org),
    ):
        organizations.update_org(
            session=MagicMock(), request=MagicMock(), user=USER, org_id=org.id, org_data=OrganizationUpdate(email=EMAIL)
        )

    assert org.email == EMAIL
    update.assert_called_once()
