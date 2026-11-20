-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- CMS photo library at scale: folders, and indexes for the library's sort and folder filter.

ALTER TABLE cms_media ADD COLUMN IF NOT EXISTS folder VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_cms_media_created_at ON cms_media (created_at);
CREATE INDEX IF NOT EXISTS idx_cms_media_folder ON cms_media (folder);
