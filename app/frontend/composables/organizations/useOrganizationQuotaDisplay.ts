// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { Ref } from 'vue';
import { useOrganizationQuota } from '~/composables/organizations/useOrganizationMembers';

/**
 * Derives the full quota display state for an organization: the underlying
 * quota state plus the seat counts, progress value, and color used by the
 * billing/members seat-usage UI.
 */
export function useOrganizationQuotaDisplay(orgRef: Ref<OrganizationRead>) {
    const { quotaState, isOverQuota } = useOrganizationQuota(orgRef);

    const progressColor = computed(() => {
        switch (quotaState.value) {
            case 'exceeded':
                return 'error';
            case 'warn':
                return 'warning';
            default:
                return 'primary';
        }
    });

    const usedSeats = computed(() => orgRef.value.premium_member_count ?? 0);
    const totalSeats = computed(() => orgRef.value.stripe_quota ?? 0);
    const progressValue = computed(() =>
        totalSeats.value > 0 ? Math.min(100, (usedSeats.value / totalSeats.value) * 100) : 0,
    );

    return { quotaState, isOverQuota, progressColor, usedSeats, totalSeats, progressValue };
}
