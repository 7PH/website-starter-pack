"""
Project-specific CMS page templates (CMS_ENABLED).

Merged over the core templates (``default``: a free page with one rich text
body). A template with the same name replaces the core one.

Fixed templates (``fixed=True``) have exactly one page, edited from the admin
and read by your own pages with ``useCmsFixed('<name>')``. Free templates can
have any number of pages, each served at its own address.

Adding a field later needs no migration: existing pages get its default.

Example::

    from .helpers.cms_templates import Template, image, richtext, text, textarea

    CMS_TEMPLATES = {
        "home": Template(
            fixed=True,
            label={"en": "Home", "fr": "Accueil"},
            fields={
                "tagline": text(
                    label={"en": "Tagline", "fr": "Accroche"},
                    max=80,
                    default="Welcome",
                    help={"en": "Shown under the site name.", "fr": "Affichée sous le nom du site."},
                ),
                "hero": image(label={"en": "Main photo", "fr": "Photo principale"}),
                "intro": textarea(label={"en": "Introduction", "fr": "Introduction"}, max=400),
                "body": richtext(label={"en": "Content", "fr": "Contenu"}),
            },
        ),
    }
"""

from .helpers.cms_templates import Template

CMS_TEMPLATES: dict[str, Template] = {}
