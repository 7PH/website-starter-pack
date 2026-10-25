# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for CMS pages: templates, validation, sanitization, permissions, drafts.

Runs the real router against an in-memory SQLite holding the two CMS tables.
"""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src import cms_templates_ext
from src.controllers import cms_pages
from src.helpers import cms_auth
from src.helpers.auth import get_current_user
from src.helpers.cms_media import media_to_public, media_to_read
from src.helpers.cms_pages import new_fixed_page, save_page, slugify
from src.helpers.cms_templates import Template, get_templates, image, richtext, text, textarea
from src.helpers.db import Base, get_session
from src.helpers.sanitize import sanitize_rich_text
from src.models.cms import CmsMediaBase, CmsPageBase
from src.schemas.cms_page import CmsPageUpdate
from src.schemas.user import UserRead

EDITOR_ID, USER_ID = 1, 2


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


TEST_TEMPLATES = {
    "home": Template(
        fixed=True,
        label={"en": "Home"},
        fields={
            "tagline": text(label={"en": "Tagline"}, max=10, default="Hi"),
            "hero": image(label={"en": "Photo"}),
        },
    ),
    "post": Template(
        label={"en": "Post"},
        fields={
            "intro": textarea(label={"en": "Intro"}, max=50),
            "body": richtext(label={"en": "Body"}, required=True, default="<p>Start</p>"),
            "photo": image(label={"en": "Photo"}),
        },
    ),
}


@pytest.fixture
def session(monkeypatch):
    # Postgres-only '::jsonb' defaults; every insert below sets these columns.
    for column in (CmsMediaBase.__table__.c.sizes, CmsPageBase.__table__.c.fields):
        monkeypatch.setattr(column, "server_default", None)
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine, tables=[CmsMediaBase.__table__, CmsPageBase.__table__])
    with Session(engine) as s:
        yield s


@pytest.fixture(autouse=True)
def templates(monkeypatch):
    monkeypatch.setattr(cms_templates_ext, "CMS_TEMPLATES", TEST_TEMPLATES)
    get_templates.cache_clear()
    yield
    get_templates.cache_clear()


@pytest.fixture
def client(session, monkeypatch):
    monkeypatch.setattr(cms_auth, "is_cms_editor", lambda _s, user_id: user_id == EDITOR_ID)
    app = FastAPI()
    app.include_router(cms_pages.router)
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def login(client: TestClient, user_id: int) -> TestClient:
    user = UserRead(id=user_id, email="u@example.com", is_admin=False, is_premium=False, auth_method="password")
    client.app.dependency_overrides[get_current_user] = lambda: user
    return client


@pytest.fixture
def editor(client):
    return login(client, EDITOR_ID)


def add_media(session: Session) -> CmsMediaBase:
    media = CmsMediaBase(
        token="tok",
        original_name="a.jpg",
        alt="A",
        width=1600,
        height=900,
        sizes=[480, 960, 1600],
        focal_x=0.5,
        focal_y=0.5,
    )
    session.add(media)
    session.commit()
    media.created_at = media.created_at or datetime.now(UTC)
    return media


def add_page(session: Session, slug: str, published: bool = True, **kw) -> CmsPageBase:
    page = CmsPageBase(
        template=kw.pop("template", "post"),
        slug=slug,
        title=slug.title(),
        fields=kw.pop("fields", {}),
        published=published,
        published_at=kw.pop("published_at", datetime.now(UTC) if published else None),
        **kw,
    )
    session.add(page)
    session.commit()
    return page


class TestSlugify:
    @pytest.mark.parametrize(
        ("title", "slug"),
        [
            ("L'été à Paris", "l-ete-a-paris"),
            ("Cœur & Âme", "coeur-ame"),
            ("  Déjà vu !!  ", "deja-vu"),
            ("Ça coûte 10 €", "ca-coute-10"),
            ("???", ""),
            ("S’ancrer", "s-ancrer"),
            ("L’été", "l-ete"),
            ("Aujourd‘hui ʼok´ `x`", "aujourd-hui-ok-x"),
        ],
    )
    def test_ascii_slugs(self, title, slug):
        assert slugify(title) == slug


class TestSanitizeRichText:
    @staticmethod
    def resolve(src: str):
        if "/cms/media/7/" not in src:
            return None
        return {"src": "https://static.example.com/cms/media/7/960.webp", "data-media-id": "7"}

    @pytest.mark.parametrize(
        "html",
        [
            "<script>alert(1)</script><p>ok</p>",
            '<p onclick="alert(1)">ok</p>',
            '<a href="javascript:alert(1)">ok</a>',
            '<a href="JaVaScRiPt:alert(1)">ok</a>',
            '<img src="x" onerror="alert(1)">',
            '<iframe src="https://evil.example"></iframe><p>ok</p>',
            '<p style="background:url(javascript:alert(1))">ok</p>',
            "<svg><script>alert(1)</script></svg>",
        ],
    )
    def test_xss_is_removed(self, html):
        result = sanitize_rich_text(html, self.resolve).lower()
        for needle in ("<script", "onerror", "onclick", "javascript:", "<iframe", "style=", "<svg"):
            assert needle not in result

    def test_script_and_style_contents_are_dropped_not_shown(self):
        html = "<p>ok</p><script>alert(1)</script><STYLE>p{color:red}</STYLE><style>never closed"
        assert sanitize_rich_text(html, self.resolve) == "<p>ok</p>"

    def test_keeps_editor_formatting(self):
        html = (
            "<h2>T</h2><h3>S</h3><p><strong>b</strong> <em>i</em><br></p><ul><li>a</li></ul>"
            '<ol start="3"><li>b</li></ol><blockquote><p>q</p></blockquote>'
        )
        assert sanitize_rich_text(html, self.resolve) == html

    def test_drops_tags_outside_the_editor(self):
        result = sanitize_rich_text("<h1>Big</h1><p><u>u</u></p><pre>c</pre>", self.resolve)
        assert "".join(result.split()) == "Big<p>u</p>c"

    @pytest.mark.parametrize("href", ["https://example.com", "http://example.com", "mailto:a@b.fr", "/contact", "#top"])
    def test_keeps_safe_links(self, href):
        assert sanitize_rich_text(f'<a href="{href}">x</a>', self.resolve) == f'<a href="{href}">x</a>'

    def test_drops_link_extras(self):
        assert sanitize_rich_text('<a href="/a" target="_blank" rel="x">x</a>', self.resolve) == '<a href="/a">x</a>'

    def test_library_image_is_stamped_and_canonicalized(self):
        result = sanitize_rich_text(
            '<img src="https://elsewhere/cms/media/7/960.webp" alt="A" data-media-id="99">', self.resolve
        )
        assert result == '<img src="https://static.example.com/cms/media/7/960.webp" alt="A" data-media-id="7">'

    @pytest.mark.parametrize("src", ["https://evil.example/cat.jpg", "data:image/png;base64,AAAA", ""])
    def test_foreign_images_are_dropped(self, src):
        assert sanitize_rich_text(f'<p>a<img src="{src}">b</p>', self.resolve) == "<p>ab</p>"


class TestTemplates:
    def test_core_default_is_merged_with_app_templates(self):
        templates = get_templates()
        assert set(templates) == {"default", "home", "post"}
        assert templates["default"].fields["body"].type == "richtext"

    def test_app_template_overrides_core(self, monkeypatch):
        override = Template(label={"en": "Mine"}, fields={})
        monkeypatch.setattr(cms_templates_ext, "CMS_TEMPLATES", {"default": override})
        get_templates.cache_clear()
        assert get_templates()["default"] is override

    def test_schema_endpoint_lists_fields_in_order(self, editor):
        templates = {t["name"]: t for t in editor.get("/cms/templates").json()}
        assert [f["name"] for f in templates["post"]["fields"]] == ["intro", "body", "photo"]
        assert templates["home"]["fixed"] is True
        assert templates["home"]["fields"][0] == {
            "name": "tagline",
            "type": "text",
            "label": {"en": "Tagline"},
            "help": {},
            "default": "Hi",
            "required": False,
            "max": 10,
        }


class TestFixedPages:
    def test_unsaved_fixed_page_serves_defaults_without_writing(self, client, session):
        data = client.get("/cms/fixed/home").json()
        assert data["id"] is None
        assert data["fields"] == {"tagline": "Hi", "hero": None}
        assert session.query(CmsPageBase).count() == 0

    def test_unknown_or_free_key_is_404(self, client):
        assert client.get("/cms/fixed/nope").status_code == 404
        assert client.get("/cms/fixed/post").status_code == 404

    def test_first_save_creates_the_row_and_image_is_expanded(self, editor, session):
        media = add_media(session)
        res = editor.patch("/cms/admin/fixed/home", json={"fields": {"tagline": "Yo", "hero": {"media_id": media.id}}})
        assert res.status_code == 200
        page = session.query(CmsPageBase).one()
        assert page.fixed_key == "home"
        assert page.fields == {"tagline": "Yo", "hero": {"media_id": media.id}}
        public = editor.get("/cms/fixed/home").json()
        assert public["fields"]["hero"] == media_to_public(media).model_dump(mode="json")
        admin = editor.get("/cms/admin/fixed/home").json()
        assert admin["fields"]["hero"] == media_to_read(media).model_dump(mode="json")

    def test_field_added_later_gets_its_default(self, client, session):
        session.add(CmsPageBase(template="home", fixed_key="home", title="", fields={"tagline": "Old"}))
        session.commit()
        assert client.get("/cms/fixed/home").json()["fields"] == {"tagline": "Old", "hero": None}

    def test_plain_text_saved_before_becoming_rich_text_is_escaped(self, client, session):
        add_page(session, "a", fields={"body": "<script>alert(1)</script>\n\nLine 1\nLine 2"})
        body = client.get("/cms/pages/by-slug/a").json()["fields"]["body"]
        assert body == "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p><p>Line 1<br>Line 2</p>"

    def test_rich_text_saved_before_becoming_plain_text_reads_as_text(self, client, session):
        session.add(
            CmsPageBase(template="home", fixed_key="home", title="", fields={"tagline": {"html": "<p>A &amp; B</p>"}})
        )
        session.commit()
        assert client.get("/cms/fixed/home").json()["fields"]["tagline"] == "A & B"

    def test_deleted_photo_reads_as_none(self, client, session):
        session.add(CmsPageBase(template="home", fixed_key="home", title="", fields={"hero": {"media_id": 404}}))
        session.commit()
        assert client.get("/cms/fixed/home").json()["fields"]["hero"] is None


class TestValidation:
    def test_unknown_fields_sent_are_dropped(self, editor, session):
        editor.patch("/cms/admin/fixed/home", json={"fields": {"tagline": "Yo", "evil": "x"}})
        assert session.query(CmsPageBase).one().fields == {"tagline": "Yo"}

    def test_stored_values_of_removed_fields_are_kept(self, editor, session):
        session.add(CmsPageBase(template="home", fixed_key="home", title="", fields={"old": "keep me"}))
        session.commit()
        editor.patch("/cms/admin/fixed/home", json={"fields": {"tagline": "Yo"}})
        assert session.query(CmsPageBase).one().fields == {"old": "keep me", "tagline": "Yo"}

    def test_page_of_a_removed_template_keeps_its_fields(self, editor, session):
        page = add_page(session, "a", fields={"body": "<p>x</p>"})
        page.template = "gone"
        session.commit()
        assert editor.patch(f"/cms/admin/pages/{page.id}", json={"title": "B", "fields": {}}).status_code == 200
        session.refresh(page)
        assert page.fields == {"body": "<p>x</p>"}

    def test_text_is_single_line_and_max_length_enforced(self, editor, session):
        editor.patch("/cms/admin/fixed/home", json={"fields": {"tagline": " a\n b "}})
        assert session.query(CmsPageBase).one().fields["tagline"] == "a b"
        res = editor.patch("/cms/admin/fixed/home", json={"fields": {"tagline": "x" * 11}})
        assert res.status_code == 422

    def test_wrong_types_and_unknown_photo_are_rejected(self, editor):
        for fields in ({"tagline": 5}, {"hero": {"media_id": 999}}, {"hero": "1"}, {"hero": {"media_id": True}}):
            assert editor.patch("/cms/admin/fixed/home", json={"fields": fields}).status_code == 422

    def test_required_field_cannot_be_emptied(self, editor, session):
        page = add_page(session, "a")
        res = editor.patch(f"/cms/admin/pages/{page.id}", json={"fields": {"body": "<p> </p>"}})
        assert res.status_code == 422

    def test_rich_text_is_sanitized_on_save(self, editor, session):
        page = add_page(session, "a")
        editor.patch(f"/cms/admin/pages/{page.id}", json={"fields": {"body": "<p>ok<script>x</script></p>"}})
        session.refresh(page)
        assert "<script" not in page.fields["body"]

    def test_rich_text_images_are_checked_against_the_library(self, editor, session):
        media = add_media(session)
        page = add_page(session, "a")
        body = f'<p>x</p><img src="https://static.example.com/cms/media/{media.id}-tok/960.webp" alt="A"><img src="https://evil.example/a.jpg"><img src="/cms/media/{media.id}-guess/960.webp">'
        editor.patch(f"/cms/admin/pages/{page.id}", json={"fields": {"body": body}})
        session.refresh(page)
        stored = page.fields["body"]["html"]
        assert stored == f'<p>x</p><img src="{media_to_public(media).src}" alt="A" data-media-id="{media.id}">'

    def test_rich_text_images_are_responsive_on_read(self, editor, session):
        media = add_media(session)
        page = add_page(session, "a")
        body = f'<p><img src="/cms/media/{media.id}-tok/960.webp" alt="Tom &amp; &quot;Jerry&quot; > cat"></p>'
        editor.patch(f"/cms/admin/pages/{page.id}", json={"fields": {"body": body}})
        read = editor.get("/cms/pages/by-slug/a").json()["fields"]["body"]
        urls = media_to_public(media).urls
        assert read == (
            f'<p><img src="{urls["1600"]}" srcset="{urls["480"]} 480w, {urls["960"]} 960w, {urls["1600"]} 1600w"'
            ' sizes="(min-width: 768px) 736px, 100vw" alt="Tom &amp; &quot;Jerry&quot; > cat" width="1600" height="900"'
            f' loading="lazy" decoding="async" data-media-id="{media.id}"></p>'
        )

    def test_rich_text_image_of_a_deleted_photo_is_dropped(self, client, session):
        add_page(session, "a", fields={"body": {"html": '<p>a<img src="x" alt="" data-media-id="404">b</p>'}})
        assert client.get("/cms/pages/by-slug/a").json()["fields"]["body"] == "<p>ab</p>"

    def test_rich_text_size_is_capped_after_sanitizing(self, editor, session):
        page = add_page(session, "a")
        url = f"/cms/admin/pages/{page.id}"
        # Mostly markup the sanitizer drops: within the input limit, the stored size is what counts.
        assert editor.patch(url, json={"fields": {"body": "<p>x</p>" + "<span></span>" * 30_000}}).status_code == 200
        res = editor.patch(url, json={"fields": {"body": "<p>" + "x" * 200_001 + "</p>"}})
        assert (res.status_code, res.json()["detail"]) == (422, "Field 'body' is too long")

    def test_rich_text_photo_count_is_capped(self, editor, session):
        media = add_media(session)
        page = add_page(session, "a")
        img = f'<img src="/cms/media/{media.id}-tok/960.webp">'
        url = f"/cms/admin/pages/{page.id}"
        assert editor.patch(url, json={"fields": {"body": img * 100}}).status_code == 200
        res = editor.patch(url, json={"fields": {"body": img * 101}})
        assert (res.status_code, res.json()["detail"]) == (422, "Field 'body' has too many photos")

    def test_required_is_only_checked_on_fields_sent(self, editor, session):
        page = add_page(session, "a", fields={"body": {"html": ""}})
        url = f"/cms/admin/pages/{page.id}"
        assert editor.patch(url, json={"fields": {"intro": "Quick edit"}}).status_code == 200
        res = editor.patch(url, json={"fields": {"intro": "Full edit", "body": ""}})
        assert (res.status_code, res.json()["detail"]) == (422, "Field 'body' is required")


class TestSeo:
    def test_auto_title_and_description(self, client, session):
        body = "<h2>Hello &amp; welcome</h2><p>" + "word " * 60 + "</p>"
        add_page(session, "a", fields={"body": {"html": body}})
        data = client.get("/cms/pages/by-slug/a").json()
        assert data["seo_title"] == "A"
        assert data["seo_description"].startswith("Hello & welcome word word")
        assert data["seo_description"].endswith("…")
        assert len(data["seo_description"]) <= 156

    def test_falls_back_to_textarea_then_keeps_explicit_values(self, client, session):
        add_page(session, "a", fields={"intro": "Short intro", "body": {"html": "<p></p>"}})
        add_page(session, "b", fields={"body": {"html": "<p>x</p>"}}, seo_title="T", seo_description="D")
        assert client.get("/cms/pages/by-slug/a").json()["seo_description"] == "Short intro"
        b = client.get("/cms/pages/by-slug/b").json()
        assert (b["seo_title"], b["seo_description"]) == ("T", "D")


class TestFreePages:
    def test_create_slugifies_and_deduplicates(self, editor, session):
        add_page(session, "a-propos")
        res = editor.post("/cms/admin/pages", json={"template": "post", "title": "À propos"})
        assert res.status_code == 201
        assert res.json()["slug"] == "a-propos-2"
        assert res.json()["published"] is False

    def test_cannot_create_fixed_or_unknown_template(self, editor):
        assert editor.post("/cms/admin/pages", json={"template": "home", "title": "x"}).status_code == 422
        assert editor.post("/cms/admin/pages", json={"template": "nope", "title": "x"}).status_code == 422

    def test_slug_clash_is_409_and_slug_is_normalized(self, editor, session):
        add_page(session, "taken")
        page = add_page(session, "mine")
        res = editor.patch(f"/cms/admin/pages/{page.id}", json={"slug": "taken"})
        assert (res.status_code, res.json()["detail"]) == (409, "slug_taken")
        assert editor.patch(f"/cms/admin/pages/{page.id}", json={"slug": "Été 2026"}).json()["slug"] == "ete-2026"

    def test_published_at_dates_each_publication(self, editor, session):
        page = add_page(session, "a", published=False)
        url = f"/cms/admin/pages/{page.id}"
        first = editor.patch(url, json={"published": True}).json()["published_at"]
        assert first is not None
        assert editor.patch(url, json={"published": True, "title": "B"}).json()["published_at"] == first
        editor.patch(url, json={"published": False})
        assert editor.patch(url, json={"published": True}).json()["published_at"] > first

    def test_reserved_slugs(self, editor, session):
        page = add_page(session, "mine")
        assert editor.patch(f"/cms/admin/pages/{page.id}", json={"slug": "apiculture"}).status_code == 422
        for slug in ("api", "admin", "administration-du-cabinet", "login", "account"):
            assert editor.patch(f"/cms/admin/pages/{page.id}", json={"slug": slug}).status_code == 422
        assert editor.patch(f"/cms/admin/pages/{page.id}", json={"slug": "accounting"}).status_code == 200
        for title, slug in (("API docs", "page-api-docs"), ("Login", "page-login"), ("Admin", "page-admin")):
            assert editor.post("/cms/admin/pages", json={"template": "post", "title": title}).json()["slug"] == slug

    def test_auto_slug_is_short_and_cut_between_words(self, editor, session):
        title = ("Un titre vraiment très long " * 7).strip()
        slug = editor.post("/cms/admin/pages", json={"template": "post", "title": title}).json()["slug"]
        assert len(slug) <= 80
        assert slugify(title).startswith(f"{slug}-")
        assert editor.post("/cms/admin/pages", json={"template": "post", "title": title}).json()["slug"] == f"{slug}-2"

    def test_unique_index_race_is_409(self, editor, session, monkeypatch):
        add_page(session, "taken")
        page = add_page(session, "mine")
        # Simulates another save taking the slug between our check and our commit.
        monkeypatch.setattr("src.helpers.cms_pages.apply_update", lambda _s, p, _d: setattr(p, "slug", "taken"))
        res = editor.patch(f"/cms/admin/pages/{page.id}", json={})
        assert (res.status_code, res.json()["detail"]) == (409, "slug_taken")

    def test_fixed_page_created_concurrently_is_409(self, session):
        session.add(new_fixed_page("home"))
        session.commit()
        with pytest.raises(HTTPException) as exc:
            save_page(session, new_fixed_page("home"), CmsPageUpdate())
        assert (exc.value.status_code, exc.value.detail) == (409, "changed_elsewhere")

    def test_list_newest_first(self, client, session):
        add_page(session, "old", position=1, published_at=datetime(2020, 1, 1, tzinfo=UTC))
        add_page(session, "new", position=2, published_at=datetime(2024, 1, 1, tzinfo=UTC))

        def slugs(**params):
            return [p["slug"] for p in client.get("/cms/pages", params={"template": "post", **params}).json()["items"]]

        assert slugs() == ["old", "new"]
        assert slugs(order="published_at") == ["new", "old"]
        assert client.get("/cms/pages", params={"template": "post", "order": "title"}).status_code in (400, 422)

    def test_import_sets_published_at(self, editor, session):
        page = add_page(session, "a", published=False)
        res = editor.patch(
            f"/cms/admin/pages/{page.id}", json={"published": True, "published_at": "2019-05-01T10:00:00Z"}
        )
        assert res.json()["published_at"].startswith("2019-05-01T10:00:00")

    def test_preview_applies_changes_without_saving(self, editor, session):
        page = add_page(session, "mine")
        body = {"title": "Draft title", "fields": {"body": "<p>Hi</p><script>x()</script>"}}
        preview = editor.post(f"/cms/admin/pages/{page.id}/preview", json=body).json()
        assert preview["title"] == "Draft title"
        assert "<script>" not in preview["fields"]["body"]
        assert editor.get(f"/cms/admin/pages/{page.id}").json()["title"] != "Draft title"

    def test_new_pages_go_last_in_their_template(self, editor, session):
        add_page(session, "a", position=5)
        assert editor.post("/cms/admin/pages", json={"template": "post", "title": "B"}).json()["id"]
        assert session.query(CmsPageBase).filter_by(slug="b").one().position == 6

    def test_reorder_and_list_by_template(self, editor, session):
        a, b = add_page(session, "a"), add_page(session, "b")
        add_page(session, "draft", published=False)
        add_page(session, "other", template="default")
        edited_at = b.updated_at
        assert editor.put("/cms/admin/pages/order", json={"ids": [b.id, a.id, 999]}).status_code == 204
        session.refresh(b)
        assert b.updated_at == edited_at
        listed = editor.get("/cms/pages", params={"template": "post"}).json()
        assert [p["slug"] for p in listed["items"]] == ["b", "a"]
        assert listed["total"] == 2
        admin_order = [p["slug"] for p in editor.get("/cms/admin/pages").json()["pages"]]
        assert admin_order.index("b") < admin_order.index("a")

    def test_fixed_pages_are_not_reachable_as_free_pages(self, editor, session):
        session.add(CmsPageBase(template="home", fixed_key="home", title="", fields={}))
        session.commit()
        fixed_id = session.query(CmsPageBase).one().id
        assert editor.get(f"/cms/admin/pages/{fixed_id}").status_code == 404
        assert editor.delete(f"/cms/admin/pages/{fixed_id}").status_code == 404

    def test_admin_list(self, editor, session):
        add_page(session, "a", published=False)
        data = editor.get("/cms/admin/pages").json()
        assert data["fixed"] == [{"key": "home", "updated_at": None}]
        assert [p["slug"] for p in data["pages"]] == ["a"]

    def test_delete(self, editor, session):
        page = add_page(session, "a")
        assert editor.delete(f"/cms/admin/pages/{page.id}").status_code == 204
        assert session.query(CmsPageBase).count() == 0


class TestConcurrentSaves:
    def test_save_with_the_loaded_updated_at_goes_through(self, editor, session):
        page = add_page(session, "a", updated_at=datetime(2026, 1, 1, 12, 0, 0, 123456))
        url = f"/cms/admin/pages/{page.id}"
        loaded = editor.get(url).json()["updated_at"]
        assert editor.patch(url, json={"title": "B", "updated_at": loaded}).status_code == 200

    def test_milliseconds_are_enough(self, editor, session):
        page = add_page(session, "a", updated_at=datetime(2026, 1, 1, 12, 0, 0, 123456))
        res = editor.patch(f"/cms/admin/pages/{page.id}", json={"title": "B", "updated_at": "2026-01-01T12:00:00.123"})
        assert res.status_code == 200

    def test_page_saved_since_loading_is_409(self, editor, session):
        page = add_page(session, "a", updated_at=datetime(2026, 1, 1, 12, 0, 0))
        res = editor.patch(f"/cms/admin/pages/{page.id}", json={"title": "B", "updated_at": "2026-01-01T11:59:00"})
        assert (res.status_code, res.json()["detail"]) == (409, "changed_elsewhere")
        session.refresh(page)
        assert page.title == "A"

    def test_fixed_page_saved_since_loading_it_unsaved_is_409(self, editor):
        url = "/cms/admin/fixed/home"
        assert editor.patch(url, json={"fields": {"tagline": "A"}, "updated_at": None}).status_code == 200
        res = editor.patch(url, json={"fields": {"tagline": "B"}, "updated_at": None})
        assert (res.status_code, res.json()["detail"]) == (409, "changed_elsewhere")

    def test_preview_never_checks(self, editor, session):
        page = add_page(session, "a")
        res = editor.post(f"/cms/admin/pages/{page.id}/preview", json={"updated_at": "2000-01-01T00:00:00"})
        assert res.status_code == 200


def count_queries(session: Session, call) -> int:
    statements = []

    def count(*_args):
        statements.append(1)

    event.listen(session.get_bind(), "before_cursor_execute", count)
    try:
        call()
    finally:
        event.remove(session.get_bind(), "before_cursor_execute", count)
    return len(statements)


class TestQueryCount:
    @staticmethod
    def add_pages_with_photos(session: Session, count: int) -> None:
        for _ in range(count):
            media = add_media(session)
            body = {"html": f'<p><img src="x" alt="" data-media-id="{media.id}"></p>'}
            add_page(
                session, f"p{media.id}", cover_media_id=media.id, fields={"body": body, "photo": {"media_id": media.id}}
            )

    def test_listing_costs_the_same_whatever_the_number_of_pages(self, client, session):
        def list_pages():
            items = client.get("/cms/pages", params={"template": "post"}).json()["items"]
            assert all(p["cover"] and p["fields"]["photo"] and "<img" in p["fields"]["body"] for p in items)

        self.add_pages_with_photos(session, 1)
        one_page = count_queries(session, list_pages)
        self.add_pages_with_photos(session, 5)
        assert count_queries(session, list_pages) == one_page == 3

    def test_page_by_slug_loads_its_photos_in_one_query(self, client, session):
        self.add_pages_with_photos(session, 1)
        slug = session.query(CmsPageBase.slug).scalar()
        assert count_queries(session, lambda: client.get(f"/cms/pages/by-slug/{slug}")) == 2


class TestPublicHidesDrafts:
    def test_by_slug(self, client, session):
        add_page(session, "draft", published=False)
        add_page(session, "live")
        assert client.get("/cms/pages/by-slug/draft").status_code == 404
        assert client.get("/cms/pages/by-slug/live").status_code == 200

    def test_editor_can_preview_a_draft(self, editor, session):
        page = add_page(session, "draft", published=False)
        assert editor.get(f"/cms/admin/pages/{page.id}").json()["slug"] == "draft"

    def test_list_and_sitemap(self, client, session):
        add_page(session, "draft", published=False)
        add_page(session, "page")
        add_page(session, "post")
        listed = client.get("/cms/pages", params={"template": "post"}).json()
        assert [p["slug"] for p in listed["items"]] == ["page", "post"]
        assert listed["total"] == 2
        assert sorted(e["loc"] for e in client.get("/cms/sitemap").json()) == ["/page", "/post"]


EDITOR_ROUTES = [
    ("get", "/cms/templates"),
    ("get", "/cms/admin/pages"),
    ("post", "/cms/admin/pages"),
    ("get", "/cms/admin/pages/1"),
    ("patch", "/cms/admin/pages/1"),
    ("post", "/cms/admin/pages/1/preview"),
    ("put", "/cms/admin/pages/order"),
    ("delete", "/cms/admin/pages/1"),
    ("get", "/cms/admin/fixed/home"),
    ("patch", "/cms/admin/fixed/home"),
]


class TestPermissions:
    def test_every_editor_route_is_covered(self):
        public = {"/cms/pages", "/cms/pages/by-slug/{slug}", "/cms/fixed/{key}", "/cms/sitemap"}
        paths = {(m.lower(), r.path) for r in cms_pages.router.routes for m in r.methods if r.path not in public}
        templated = {(m, p.replace("1", "{page_id}").replace("home", "{key}")) for m, p in EDITOR_ROUTES}
        assert paths == templated

    @pytest.mark.parametrize(("method", "path"), EDITOR_ROUTES)
    def test_anonymous_is_401(self, client, method, path):
        assert client.request(method, path, json={}).status_code == 401

    @pytest.mark.parametrize(("method", "path"), EDITOR_ROUTES)
    def test_plain_user_is_403(self, client, method, path):
        assert login(client, USER_ID).request(method, path, json={}).status_code == 403

    @pytest.mark.parametrize(("method", "path"), EDITOR_ROUTES)
    def test_editor_gets_through(self, editor, session, method, path):
        add_page(session, "a")
        assert editor.request(method, path, json={"template": "post", "title": "x", "ids": []}).status_code < 400

    @pytest.mark.parametrize(
        "path", ["/cms/pages/by-slug/a", "/cms/fixed/home", "/cms/pages?template=post", "/cms/sitemap"]
    )
    def test_public_routes_need_no_login(self, client, session, path):
        add_page(session, "a")
        assert client.get(path).status_code == 200
