import type { ComputedRef } from 'vue';
import type { MainNavItem } from './main-nav';

/**
 * Projects implement this composable to add custom nav items to PageHeader.
 * Full control over logic - can use auth state, org data, async fetches, etc.
 *
 * @example
 * export function useMainNavExtensions(): ComputedRef<MainNavItem[]> {
 *     const auth = useAuth();
 *     return computed(() => {
 *         if (!auth.user?.organizations?.length) return [];
 *         const org = auth.user.organizations[0];
 *         return [{
 *             label: 'Booking Pages',
 *             icon: 'i-lucide-calendar',
 *             to: `/organizations/${org.id}/booking-pages`,
 *             order: 10,
 *         }];
 *     });
 * }
 */
export function useMainNavExtensions(): ComputedRef<MainNavItem[]> {
    return computed(() => []);
}
