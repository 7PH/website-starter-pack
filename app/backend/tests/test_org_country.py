# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Organization country is an ISO 3166-1 alpha-2 code, never a truncated country name."""

import pytest
from pydantic import ValidationError

from src.schemas.organization import OrganizationUpdate


@pytest.mark.parametrize(("given", "stored"), [("fr", "FR"), ("US", "US"), ("", ""), (None, None)])
def test_accepts_codes(given, stored):
    assert OrganizationUpdate(country=given).country == stored


@pytest.mark.parametrize("given", ["France", "F", "F1", "É1"])
def test_rejects_anything_else(given):
    with pytest.raises(ValidationError):
        OrganizationUpdate(country=given)
