-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- CMS mode (CMS_ENABLED): editors, photo library and pages. create_all creates these
-- tables on startup, flag on or off. This file is for apps that create tables by hand.

CREATE TABLE IF NOT EXISTS cms_editors (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Files live in static/cms/media/<id>/<width>.webp. The original upload is not kept.
CREATE TABLE IF NOT EXISTS cms_media (
    id SERIAL PRIMARY KEY,
    original_name VARCHAR(255) NOT NULL,
    alt VARCHAR(300) NOT NULL DEFAULT '',
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    sizes JSONB NOT NULL DEFAULT '[]'::jsonb,
    focal_x DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    focal_y DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cms_pages (
    id SERIAL PRIMARY KEY,
    template VARCHAR(64) NOT NULL,
    fixed_key VARCHAR(64),
    slug VARCHAR(200),
    title VARCHAR(200) NOT NULL DEFAULT '',
    fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    published BOOLEAN NOT NULL DEFAULT false,
    show_in_blog BOOLEAN NOT NULL DEFAULT false,
    seo_title VARCHAR(200) NOT NULL DEFAULT '',
    seo_description VARCHAR(300) NOT NULL DEFAULT '',
    cover_media_id INTEGER REFERENCES cms_media(id) ON DELETE SET NULL,
    position INTEGER NOT NULL DEFAULT 0,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cms_pages_slug ON cms_pages (slug) WHERE slug IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_cms_pages_fixed_key ON cms_pages (fixed_key) WHERE fixed_key IS NOT NULL;
