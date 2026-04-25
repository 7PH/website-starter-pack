// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Pure helpers for the bug-report composer.
 * Kept outside the Vue component so they're unit-testable without mounting.
 */

export interface CapturedContext {
    url: string;
    userAgent: string;
    viewport: string;
}

/** Capture the current URL path (no query string, no fragment), user-agent, and viewport. */
export function captureContext(params: {
    locationHref: string;
    userAgent: string;
    innerWidth: number;
    innerHeight: number;
}): CapturedContext {
    const loc = new URL(params.locationHref);
    return {
        url: loc.origin + loc.pathname, // strip ?query and #fragment client-side
        userAgent: params.userAgent,
        viewport: `${params.innerWidth}×${params.innerHeight}`,
    };
}

/** Build the markdown body a bug report submits: description + auto-captured context. */
export function buildBugReportBody(description: string, captured: CapturedContext): string {
    return [
        '**Description**',
        description.trim(),
        '',
        '---',
        '_Auto-captured context:_',
        `- URL: ${captured.url}`,
        `- User-agent: ${captured.userAgent}`,
        `- Viewport: ${captured.viewport}`,
    ].join('\n');
}

/** Auto-generate a subject from the first 60 chars of the content, with a prefix. */
export function buildAutoSubject(content: string, prefix: string): string {
    const snippet = content.trim().slice(0, 60).trim();
    return `${prefix}${snippet}`;
}
