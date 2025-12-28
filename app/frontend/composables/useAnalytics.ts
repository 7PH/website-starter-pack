// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Analytics composable for Umami integration.
 * Provides event tracking when Umami is enabled.
 *
 * @example
 * const { trackEvent } = useAnalytics();
 *
 * // Track a button click
 * trackEvent('button_click', { button: 'signup' });
 *
 * // Track a page view with custom data
 * trackEvent('page_view', { page: 'pricing', variant: 'a' });
 */

// Extend window type to include umami
declare global {
    interface Window {
        umami?: {
            track: (eventName: string, eventData?: Record<string, unknown>) => void;
        };
    }
}

export function useAnalytics() {
    const config = useRuntimeConfig();

    /**
     * Check if analytics is enabled.
     */
    const isEnabled = computed(() => {
        return config.public.umamiEnabled === true;
    });

    /**
     * Track a custom event.
     *
     * @param eventName - Name of the event
     * @param eventData - Optional data to attach to the event
     */
    function trackEvent(eventName: string, eventData: Record<string, unknown> = {}): void {
        if (import.meta.server) {
            return;
        }

        if (!isEnabled.value) {
            return;
        }

        if (!window.umami) {
            console.debug('Umami not loaded, skipping event:', eventName);
            return;
        }

        try {
            window.umami.track(eventName, eventData);
        } catch (error) {
            console.error('Analytics error:', error);
        }
    }

    /**
     * Track a page view with custom properties.
     * Note: Umami automatically tracks page views, this is for custom tracking.
     */
    function trackPageView(pageName: string, properties: Record<string, unknown> = {}): void {
        trackEvent('page_view', { page: pageName, ...properties });
    }

    return {
        isEnabled,
        trackEvent,
        trackPageView,
    };
}
