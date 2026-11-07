// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { ANALYTICS } from '~/config/analytics-ext';
import type { AnalyticsEventData } from '~/types/analytics';

/**
 * Event tracking through the provider set up in config/analytics-ext.ts.
 *
 * @example
 * const { trackEvent } = useAnalytics();
 * trackEvent('button_click', { button: 'signup' });
 */
export function useAnalytics() {
    const isEnabled = computed(() => ANALYTICS.scripts.length > 0);

    function trackEvent(eventName: string, eventData: AnalyticsEventData = {}): void {
        if (import.meta.server || !isEnabled.value) {
            return;
        }
        try {
            ANALYTICS.track(eventName, eventData);
        } catch (error) {
            console.error('Analytics error:', error);
        }
    }

    /** Providers track page views on their own, this is for custom tracking. */
    function trackPageView(pageName: string, properties: AnalyticsEventData = {}): void {
        trackEvent('page_view', { page: pageName, ...properties });
    }

    return {
        isEnabled,
        trackEvent,
        trackPageView,
    };
}
