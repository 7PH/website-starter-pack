"""
Project-specific security headers overrides.

Customize security headers by modifying SECURITY_HEADERS_OVERRIDE below.
These values will be merged with the defaults from security_headers.py.
"""

SECURITY_HEADERS_OVERRIDE: dict[str, str] = {
    # Examples:
    # "X-Frame-Options": "",  # Empty string removes the header (allow iframes)
    # "X-Frame-Options": "DENY",  # Override default value
    # "Cross-Origin-Resource-Policy": "cross-origin",  # Add new header
}
