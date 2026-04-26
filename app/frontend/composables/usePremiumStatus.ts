// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Lightweight premium-entitlement composable for `<PremiumGate>` and any
 * UI that needs to read or refresh the user's premium status.
 *
 * Reads from the same source as `useStripe.isPremium` (auth.user.is_premium)
 * so the two can't disagree. Use this one for cheap entitlement reads;
 * use `useStripe()` when you need plan name / expiry / billing portal.
 *
 * Auto-refreshes on `visibilitychange` (tab regains focus) so users who
 * subscribed via Stripe Checkout in a popup tab see the gate unlock when
 * they return. Throttled client-side to once per 5 minutes.
 *
 * @example
 * const { isPremium, refresh } = usePremiumStatus();
 * if (isPremium.value) { ... }
 */

// Module-level state: shared across all callers in the app.
let lastRefreshAt = 0;
let listenerAttached = false;
const COOLDOWN_MS = 5 * 60 * 1000;

export function usePremiumStatus() {
    const auth = useAuth();

    const isPremium = computed(() => auth.user?.is_premium ?? false);

    async function refresh(): Promise<void> {
        if (Date.now() - lastRefreshAt < COOLDOWN_MS) {
            return;
        }
        lastRefreshAt = Date.now();
        await auth.refreshToken();
    }

    if (import.meta.client && !listenerAttached) {
        listenerAttached = true;
        useEventListener(document, 'visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                refresh();
            }
        });
    }

    return {
        isPremium,
        refresh,
    };
}
