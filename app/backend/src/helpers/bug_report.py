# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""PII hygiene helpers for bug-report conversation bodies."""

import re

# Matches a line like "- URL: https://example.com/path?token=abc" in the
# auto-captured context block the frontend appends to bug reports.
_URL_LINE_RE = re.compile(r"^(- URL: )(\S+)$", re.MULTILINE)


def strip_url_query_in_body(content: str) -> str:
    """Truncate any auto-captured URL at the first '?' or '#'.

    URLs often carry tokens, signed-URL params, or session identifiers.
    The path is enough for triage; the admin can ask the reporter for
    specific query params if they need them.
    """

    def _truncate(match: re.Match[str]) -> str:
        prefix, url = match.group(1), match.group(2)
        cut = len(url)
        for sep in ("?", "#"):
            idx = url.find(sep)
            if idx != -1 and idx < cut:
                cut = idx
        return f"{prefix}{url[:cut]}"

    return _URL_LINE_RE.sub(_truncate, content)
