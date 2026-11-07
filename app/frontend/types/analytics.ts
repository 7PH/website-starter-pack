// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

export type AnalyticsEventData = Record<string, unknown>;

export interface AnalyticsConfig {
    /** Head script entries (src + attributes, or innerHTML for inline init code), added to every page. */
    scripts: Record<string, string | boolean>[];
    /** Origins the provider loads from or sends to, added to the CSP script-src and connect-src. */
    origins: string[];
    /** Sends a custom event to the provider. Called by useAnalytics().trackEvent(), client-side only. */
    track: (eventName: string, eventData: AnalyticsEventData) => void;
}
