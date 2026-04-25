"""
Project-specific constants.

Extend the core constants with values specific to this app.
"""

from .constants import CoreConversationSubtype

# User-initiable conversation subtypes accepted on POST /conversations.
# Default: only the core values. To add project-specific subtypes, widen the
# alias with a Literal — values flow through Pydantic validation AND the
# generated TS types via ./scripts/_core/convert-models.sh::
#
#     from typing import Literal
#     type UserInitiableSubtype = CoreConversationSubtype | Literal["organization_request", "billing"]
#
# Admin-only subtypes should NOT be added here — set them server-side instead
# so a client can never assert one.
type UserInitiableSubtype = CoreConversationSubtype
