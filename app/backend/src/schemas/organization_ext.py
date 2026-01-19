"""
Project-specific organization custom data schema.
Customize the OrganizationCustomData class with your fields.

Example for a school app:
    class OrganizationCustomData(BaseModel):
        rne: str | None = Field(default=None, max_length=8)
        school_type: str | None = None
"""

from pydantic import BaseModel


class OrganizationCustomData(BaseModel):
    """Custom fields for organizations. Add your project-specific fields here."""

    pass  # Add fields like: rne: str | None = None
