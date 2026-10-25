# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the CMS photo library: image processing, permissions and the delete-in-use guard."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

import io
import logging
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from PIL import Image, ImageCms

from src import main
from src.controllers import cms_media as controller
from src.helpers import cms_media
from src.helpers.auth import get_current_user
from src.helpers.cms_auth import get_current_cms_editor
from src.helpers.db import get_session
from src.models.cms import CmsMediaBase
from src.models.user import UserBase
from src.schemas.user import UserRead


def _image_bytes(size=(100, 50), mode="RGB", fmt="JPEG", color=(200, 30, 30), **save_kwargs) -> bytes:
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, fmt, **save_kwargs)
    return buf.getvalue()


def _decode(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img


class TestProcessImage:
    def test_generates_widths_not_larger_than_original(self):
        _, _, files = cms_media.process_image(_image_bytes(size=(1700, 1000)))
        assert sorted(files) == [480, 960, 1600]
        assert _decode(files[480]).size == (480, 282)
        assert all(_decode(data).format == "WEBP" for data in files.values())

    def test_small_image_keeps_its_own_width(self):
        width, height, files = cms_media.process_image(_image_bytes(size=(300, 200)))
        assert (width, height) == (300, 200)
        assert list(files) == [300]

    def test_applies_exif_orientation(self):
        exif = Image.Exif()
        exif[0x0112] = 6  # Rotated 90° clockwise, as phones save portrait shots.
        width, height, files = cms_media.process_image(_image_bytes(size=(600, 400), exif=exif.tobytes()))
        assert (width, height) == (400, 600)
        assert _decode(files[400]).size == (400, 600)

    def test_downscales_large_photo_on_its_upright_size(self):
        exif = Image.Exif()
        exif[0x0112] = 6
        width, height, files = cms_media.process_image(_image_bytes(size=(4000, 3000), exif=exif.tobytes()))
        assert (width, height) == (2400, 3200)
        assert sorted(files) == [480, 960, 1600, 2400]
        assert _decode(files[2400]).size == (2400, 3200)

    def test_very_tall_image_fits_webp_limits(self):
        width, height, files = cms_media.process_image(_image_bytes(size=(400, 40000), fmt="PNG"))
        assert height <= cms_media.WEBP_MAX_SIDE
        assert _decode(files[width]).size == (width, height)

    def test_16_bit_grayscale_keeps_its_tones(self):
        _, _, files = cms_media.process_image(_image_bytes(size=(100, 100), mode="I;16", fmt="PNG", color=32768))
        red, _, _ = _decode(files[100]).getpixel((50, 50))
        assert 110 < red < 145

    def test_16_bit_is_shrunk_before_its_tones_are_rescaled(self, monkeypatch):
        sizes, point = [], Image.Image.point
        monkeypatch.setattr(Image.Image, "point", lambda img, *a, **k: sizes.append(img.size) or point(img, *a, **k))
        # Wide enough that Pillow can't resize it in its 16-bit mode.
        width, _, _ = cms_media.process_image(_image_bytes(size=(15000, 20), mode="I;16", fmt="PNG", color=32768))
        assert width == 2400
        assert sizes == [(2400, 3)]

    def test_palette_image_is_smoothed_when_shrunk(self):
        img = Image.new("P", (4800, 10))
        img.putpalette([0, 0, 0, 255, 255, 255])
        img.putdata([x % 2 for _ in range(10) for x in range(4800)])  # 1px black and white stripes
        buf = io.BytesIO()
        img.save(buf, "PNG")
        _, _, files = cms_media.process_image(buf.getvalue())
        red, _, _ = _decode(files[2400]).getpixel((1200, 2))
        assert 100 < red < 155

    def test_at_most_two_images_processed_at_once(self, monkeypatch):
        running, peak, lock, to_srgb = 0, 0, threading.Lock(), cms_media._to_srgb

        def slow_to_srgb(img, mode):
            nonlocal running, peak
            with lock:
                running += 1
                peak = max(peak, running)
            time.sleep(0.05)
            with lock:
                running -= 1
            return to_srgb(img, mode)

        monkeypatch.setattr(cms_media, "_to_srgb", slow_to_srgb)
        data = _image_bytes()
        with ThreadPoolExecutor(4) as pool:
            list(pool.map(lambda _: cms_media.process_image(data), range(4)))
        assert peak == 2

    def test_strips_metadata(self):
        exif = Image.Exif()
        exif[0x010F] = "PhoneMaker"
        exif[0x8825] = {2: (48.0, 51.0, 24.0)}  # GPS latitude
        srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        data = _image_bytes(size=(500, 300), exif=exif.tobytes(), icc_profile=srgb)
        _, _, files = cms_media.process_image(data)
        out = _decode(files[480])
        assert not out.getexif()
        assert "exif" not in out.info
        assert "icc_profile" not in out.info
        assert "xmp" not in out.info
        assert b"PhoneMaker" not in files[480]

    def test_png_alpha_is_kept(self):
        _, _, files = cms_media.process_image(_image_bytes(size=(500, 300), mode="RGBA", fmt="PNG", color=(0, 0, 0, 0)))
        out = _decode(files[480])
        assert out.mode == "RGBA"
        assert out.getpixel((10, 10))[3] == 0

    def test_png_alpha_survives_color_profile_conversion(self):
        img = Image.new("RGBA", (400, 300), (0, 0, 255, 255))
        img.paste((0, 0, 0, 0), (0, 0, 200, 300))  # Left half transparent.
        buf = io.BytesIO()
        img.save(buf, "PNG", icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
        _, _, files = cms_media.process_image(buf.getvalue())
        out = _decode(files[400])
        assert out.mode == "RGBA"
        assert out.getpixel((50, 150))[3] == 0
        assert out.getpixel((350, 150))[3] == 255

    def test_opaque_png_becomes_rgb(self):
        _, _, files = cms_media.process_image(_image_bytes(size=(500, 300), mode="RGB", fmt="PNG"))
        assert _decode(files[480]).mode == "RGB"

    def test_cmyk_jpeg_is_converted(self):
        _, _, files = cms_media.process_image(_image_bytes(mode="CMYK", color=(0, 0, 0, 0)))
        assert _decode(files[100]).mode == "RGB"

    def test_rejects_too_big_file(self, monkeypatch):
        monkeypatch.setattr(cms_media, "MAX_UPLOAD_BYTES", 100)
        with pytest.raises(HTTPException) as exc:
            cms_media.process_image(_image_bytes())
        assert exc.value.status_code == 413

    def test_rejects_wrong_type_whatever_the_name(self):
        for data in (b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", b"GIF89a" + b"\x00" * 50, b"plain text"):
            with pytest.raises(HTTPException) as exc:
                cms_media.process_image(data)
            assert exc.value.status_code == 415

    def test_rejects_decompression_bomb_before_decoding(self, monkeypatch):
        monkeypatch.setattr(cms_media, "MAX_PIXELS", 100 * 100)
        data = _image_bytes(size=(101, 100), fmt="PNG")
        with (
            patch.object(Image.Image, "load", side_effect=AssertionError("decoded")),
            pytest.raises(HTTPException) as exc,
        ):
            cms_media.process_image(data)
        assert exc.value.status_code == 422

    def test_rejects_truncated_image(self):
        with pytest.raises(HTTPException) as exc:
            cms_media.process_image(_image_bytes(size=(800, 600))[:300])
        assert exc.value.status_code == 400

    def test_rejects_format_mismatch(self):
        """Magic says JPEG but the body is a PNG past the header: only the JPEG decoder may run."""
        data = _image_bytes(fmt="JPEG")[:4] + _image_bytes(fmt="PNG")
        with pytest.raises(HTTPException) as exc:
            cms_media.process_image(data)
        assert exc.value.status_code in (400, 415)


class TestHelpers:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("../../etc/passwd.jpg", "passwd.jpg"),
            ("C:\\Users\\me\\IMG_0001.JPG", "IMG_0001.JPG"),
            ("bad\x00\nname.png", "badname.png"),
            ("", "photo"),
            (None, "photo"),
            ("a" * 300 + ".jpg", "a" * 255),
        ],
    )
    def test_safe_original_name(self, name, expected):
        assert cms_media.safe_original_name(name) == expected

    def test_media_to_read_builds_absolute_urls(self, monkeypatch):
        monkeypatch.setattr(cms_media, "STATIC_ORIGIN", "https://static.example.com")
        media = _media(sizes=[480, 960])
        read = cms_media.media_to_read(media)
        assert read.urls == {
            "480": "https://static.example.com/cms/media/7-tok/480.webp",
            "960": "https://static.example.com/cms/media/7-tok/960.webp",
        }
        assert read.src == "https://static.example.com/cms/media/7-tok/960.webp"

    def test_public_shape_hides_library_details(self):
        public = cms_media.media_to_public(_media()).model_dump()
        assert "original_name" not in public and "created_at" not in public
        assert cms_media.media_to_read(_media()).model_dump().items() > public.items()

    def test_media_ids_in_fields(self):
        fields = {
            "hero": {"media_id": 5},
            "body": '<p>x</p><img src="a" data-media-id="50"><img data-media-id="7">',
            "tagline": "media_id 9",
            "other": {"media_id": "6"},
            "flag": {"media_id": True},
            "gallery": [{"media_id": 11}, {"caption": "x", "photo": {"media_id": 12}}],
            "sections": [{"text": '<img data-media-id="13">'}],
        }
        assert cms_media.media_ids_in_fields(fields) == {5, 50, 7, 11, 12, 13}

    def test_pillow_not_imported_until_an_upload(self):
        """Apps with CMS off import the controller but must not pay for Pillow."""
        code = "import sys, src.controllers.cms_media; assert 'PIL' not in sys.modules"
        subprocess.run([sys.executable, "-c", code], check=True, cwd=Path(__file__).parent.parent, env=os.environ)

    def test_pages_using_media(self):
        session = MagicMock()
        session.query.return_value.all.return_value = [
            (1, "About", None, 5, {}),
            (2, "", "home", None, {"hero": {"media_id": 5}}),
            (3, "Blog post", None, None, {"body": '<img data-media-id="5">'}),
            (4, "Other", None, 50, {"body": '<img data-media-id="55">'}),
        ]
        assert [p.model_dump() for p in cms_media.pages_using_media(session, 5)] == [
            {"id": 1, "title": "About", "fixed_key": None},
            {"id": 2, "title": "home", "fixed_key": "home"},
            {"id": 3, "title": "Blog post", "fixed_key": None},
        ]


def _media(media_id=7, sizes=None) -> CmsMediaBase:
    return CmsMediaBase(
        id=media_id,
        token="tok",
        original_name="photo.jpg",
        alt="",
        width=960,
        height=640,
        sizes=sizes or [480, 960],
        focal_x=0.5,
        focal_y=0.5,
        created_at=datetime.now(UTC),
    )


ROLES = {"user": (False, False), "editor": (False, True), "admin": (True, False)}


@pytest.fixture
def make_client(temp_static_dir):
    """TestClient on the media router, logged in as a role. DB lookups are mocked."""

    def _make(role: str, session: MagicMock | None = None):
        is_admin, is_editor = ROLES[role]
        session = session or MagicMock()
        db_user = UserBase(id=1, is_admin=is_admin)
        # session.get serves both the editor lookup (cms_auth) and the media lookup (controller).
        session.get.side_effect = lambda model, key: (
            (object() if is_editor else None) if model.__name__ == "CmsEditorBase" else _media(key)
        )
        app = FastAPI()
        app.include_router(controller.router)
        # The app's real handlers: they reshape error bodies, which clients depend on.
        for exc_class, handler in main.app.exception_handlers.items():
            app.add_exception_handler(exc_class, handler)
        app.dependency_overrides[get_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: UserRead(
            id=1, email="u@example.com", first_name="A", last_name="B", is_admin=is_admin, is_premium=False
        )
        client = TestClient(app)
        patcher = patch("src.crud.users.get_user_by_id", return_value=db_user)
        patcher.start()
        return client, session, patcher

    patchers = []

    def _tracked(role, session=None):
        client, session, patcher = _make(role, session)
        patchers.append(patcher)
        return client, session

    yield _tracked
    for p in patchers:
        p.stop()


class TestPermissions:
    def test_every_route_requires_cms_editor(self):
        for route in controller.router.routes:
            deps = [d.call for d in route.dependant.dependencies]
            assert get_current_cms_editor in deps, route.path

    @pytest.mark.parametrize(
        ("method", "path", "kwargs"),
        [
            ("get", "/cms/media", {}),
            ("get", "/cms/media/7", {}),
            ("patch", "/cms/media/7", {"json": {"alt": "x"}}),
            ("delete", "/cms/media/7", {}),
            ("post", "/cms/media", {"files": {"file": ("a.jpg", b"x", "image/jpeg")}}),
        ],
    )
    def test_plain_user_is_refused(self, make_client, method, path, kwargs):
        client, session = make_client("user")
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 403
        session.commit.assert_not_called()

    @pytest.mark.parametrize("role", ["editor", "admin"])
    def test_editor_and_admin_can_read(self, make_client, role):
        client, _ = make_client(role)
        response = client.get("/cms/media/7")
        assert response.status_code == 200
        assert response.json()["id"] == 7


class TestEndpoints:
    def test_upload_stores_webp_files_and_row(self, make_client, temp_static_dir, caplog):
        # INFO on, or the real logger skips formatting and a bad logging call goes unnoticed.
        caplog.set_level(logging.INFO)
        client, session = make_client("editor")

        def flush():
            session.add.call_args.args[0].id = 42

        def refresh(media):
            # Server defaults a real refresh would load.
            media.created_at, media.focal_x, media.focal_y = datetime.now(UTC), 0.5, 0.5

        session.flush.side_effect = flush
        session.refresh.side_effect = refresh
        response = client.post(
            "/cms/media",
            files={"file": ("../IMG_1.jpg", _image_bytes(size=(1000, 500)), "image/jpeg")},
            data={"alt": "  A garden  "},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["id"] == 42
        assert body["original_name"] == "IMG_1.jpg"
        assert body["alt"] == "A garden"
        assert list(body["urls"]) == ["480", "960"]
        (folder,) = (temp_static_dir / "cms/media").iterdir()
        token = folder.name.removeprefix("42-")
        assert len(token) == 12 and folder.name == f"42-{token}"
        assert sorted(p.name for p in folder.iterdir()) == ["480.webp", "960.webp"]
        assert body["src"].endswith(f"/cms/media/42-{token}/960.webp")
        session.commit.assert_called_once()
        assert "CMS media 42 uploaded" in caplog.text

    def test_upload_rejected_writes_nothing(self, make_client, temp_static_dir):
        client, session = make_client("editor")
        response = client.post("/cms/media", files={"file": ("a.jpg", b"not an image", "image/jpeg")})
        assert response.status_code == 415
        session.add.assert_not_called()
        assert not (temp_static_dir / "cms").exists()

    def test_patch_updates_only_given_fields(self, make_client):
        client, session = make_client("editor")
        media = _media()
        session.get.side_effect = lambda model, key: object() if model.__name__ == "CmsEditorBase" else media
        response = client.patch("/cms/media/7", json={"focal_x": 0.2})
        assert response.status_code == 200
        assert (media.focal_x, media.focal_y, media.alt) == (0.2, 0.5, "")

    def test_patch_rejects_out_of_range_focal(self, make_client):
        client, _ = make_client("editor")
        # Core's validation handler answers 400, apps may replace it with one answering 422.
        assert client.patch("/cms/media/7", json={"focal_y": 1.5}).status_code in (400, 422)

    def test_delete_in_use_returns_409_with_titles(self, make_client, temp_static_dir):
        client, session = make_client("editor")
        (temp_static_dir / "cms/media/7-tok").mkdir(parents=True)
        session.query.return_value.all.return_value = [(3, "Home", "home", 7, {}), (4, "About", None, None, {})]
        response = client.delete("/cms/media/7")
        assert response.status_code == 409
        assert response.json()["pages"] == [{"id": 3, "title": "Home", "fixed_key": "home"}]
        session.delete.assert_not_called()
        assert (temp_static_dir / "cms/media/7-tok").exists()

    def test_delete_warns_when_files_stay(self, make_client, temp_static_dir, caplog):
        caplog.set_level(logging.INFO)
        client, _ = make_client("editor")
        (temp_static_dir / "cms/media/7-tok").mkdir(parents=True)
        with patch.object(controller, "pages_using_media", return_value=[]), patch("shutil.rmtree"):
            assert client.delete("/cms/media/7").status_code == 204
        assert "folder still on disk" in caplog.text

    def test_delete_removes_row_and_files(self, make_client, temp_static_dir):
        client, session = make_client("editor")
        (temp_static_dir / "cms/media/7-tok").mkdir(parents=True)
        (temp_static_dir / "cms/media/7-tok/480.webp").write_bytes(b"x")
        with patch.object(controller, "pages_using_media", return_value=[]):
            response = client.delete("/cms/media/7")
        assert response.status_code == 204
        session.delete.assert_called_once()
        assert not (temp_static_dir / "cms/media/7-tok").exists()
