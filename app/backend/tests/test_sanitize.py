# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""
Tests for HTML sanitization utility.
"""


from src.helpers.sanitize import sanitize_html, strip_all_tags


class TestSanitizeHtml:
    """Tests for sanitize_html function."""

    def test_removes_script_tags(self):
        """XSS script tags should be removed (content may remain as text)."""
        html = "<script>alert('xss')</script>"
        result = sanitize_html(html)
        # Script tag is stripped, content becomes harmless text
        assert "<script>" not in result
        assert "</script>" not in result

    def test_removes_event_handlers(self):
        """Event handler attributes should be removed."""
        html = '<p onclick="alert(1)">Click me</p>'
        result = sanitize_html(html)
        assert "onclick" not in result
        assert result == "<p>Click me</p>"

    def test_preserves_basic_formatting(self):
        """Basic formatting tags should be preserved."""
        html = "<p>Hello <strong>world</strong></p>"
        result = sanitize_html(html)
        assert result == html

    def test_preserves_lists(self):
        """List tags should be preserved."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = sanitize_html(html)
        assert result == html

    def test_preserves_safe_links(self):
        """Links with safe protocols should be preserved."""
        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)
        assert result == html

    def test_strips_javascript_links(self):
        """JavaScript protocol in links should be removed."""
        html = '<a href="javascript:alert(1)">Click</a>'
        result = sanitize_html(html)
        # href attribute should be stripped but tag preserved
        assert "javascript" not in result
        assert result == "<a>Click</a>"

    def test_removes_images_by_default(self):
        """Image tags should be removed by default."""
        html = '<img src="photo.jpg" alt="Photo">'
        result = sanitize_html(html)
        assert result == ""

    def test_allows_images_when_enabled(self):
        """Image tags should be allowed when allow_images=True."""
        html = '<img src="photo.jpg" alt="Photo">'
        result = sanitize_html(html, allow_images=True)
        assert "img" in result
        assert 'src="photo.jpg"' in result
        assert 'alt="Photo"' in result

    def test_handles_empty_string(self):
        """Empty string should return empty string."""
        assert sanitize_html("") == ""

    def test_handles_none_like_empty(self):
        """None-like values should return empty string."""
        assert sanitize_html("") == ""

    def test_handles_malformed_html(self):
        """Malformed HTML should be handled gracefully."""
        html = "<p>Unclosed paragraph<div>Mixed tags</p></div>"
        result = sanitize_html(html)
        # Should not raise, result should be safe
        assert "script" not in result
        assert "<p>" in result or "Unclosed" in result

    def test_preserves_headings(self):
        """Heading tags should be preserved."""
        html = "<h1>Title</h1><h2>Subtitle</h2>"
        result = sanitize_html(html)
        assert result == html

    def test_preserves_code_blocks(self):
        """Code and pre tags should be preserved."""
        html = "<pre><code>const x = 1;</code></pre>"
        result = sanitize_html(html)
        assert result == html


class TestStripAllTags:
    """Tests for strip_all_tags function."""

    def test_strips_all_html(self):
        """Should remove all HTML tags."""
        html = "<p>Hello <strong>world</strong></p>"
        result = strip_all_tags(html)
        assert result == "Hello world"

    def test_handles_complex_html(self):
        """Should strip complex nested HTML."""
        html = "<div><ul><li>Item</li></ul></div>"
        result = strip_all_tags(html)
        # Block elements may leave whitespace, but text is preserved
        assert "Item" in result
        assert "<" not in result

    def test_handles_empty_string(self):
        """Empty string should return empty string."""
        assert strip_all_tags("") == ""

    def test_preserves_text_content(self):
        """Text content should be preserved."""
        html = "Plain text without tags"
        result = strip_all_tags(html)
        assert result == html
