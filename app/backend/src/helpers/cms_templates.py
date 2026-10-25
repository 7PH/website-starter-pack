# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS page templates (CMS_ENABLED): the fields each kind of page has.

Apps declare their own templates in ``cms_templates_ext.py``; they are merged
over the core ones below. Labels and help texts are ``{locale: text}`` dicts.
"""

from dataclasses import dataclass, field
from functools import cache
from typing import Literal

type Localized = dict[str, str]
type FieldType = Literal["text", "textarea", "richtext", "image"]


@dataclass(frozen=True)
class Field:
    type: FieldType
    label: Localized
    help: Localized = field(default_factory=dict)
    default: str | None = None
    required: bool = False
    max: int | None = None


@dataclass(frozen=True)
class Template:
    label: Localized
    fields: dict[str, Field]
    # Fixed: exactly one page (home, site settings...), not routed. Free: any number of pages, each at its slug.
    fixed: bool = False


def text(
    label: Localized, max: int = 200, default: str = "", help: Localized | None = None, required: bool = False
) -> Field:
    """Single line of text."""
    return Field("text", label, help or {}, default, required, max)


def textarea(
    label: Localized, max: int = 1000, default: str = "", help: Localized | None = None, required: bool = False
) -> Field:
    """Plain text over several lines."""
    return Field("textarea", label, help or {}, default, required, max)


def richtext(label: Localized, default: str = "", help: Localized | None = None, required: bool = False) -> Field:
    """Formatted text (headings, bold, lists, links, photos). Stored as ``{"html": <sanitized HTML>}``."""
    return Field("richtext", label, help or {}, default, required)


def image(label: Localized, help: Localized | None = None, required: bool = False) -> Field:
    """A photo from the library. Stored as ``{"media_id": int}``."""
    return Field("image", label, help or {}, None, required)


CORE_TEMPLATES: dict[str, Template] = {
    "default": Template(
        label={"en": "Page", "fr": "Page"},
        fields={"body": richtext(label={"en": "Content", "fr": "Contenu"})},
    ),
}


@cache
def get_templates() -> dict[str, Template]:
    # Imported here: the ext file imports the field helpers above.
    from ..cms_templates_ext import CMS_TEMPLATES

    return {**CORE_TEMPLATES, **CMS_TEMPLATES}
