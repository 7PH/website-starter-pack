// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

export interface MainNavItem {
    /** Display label */
    label: string;
    /** Icon name (e.g., 'i-lucide-calendar') */
    icon: string;
    /** Route path */
    to: string;
    /** Sort order (lower = left in nav) */
    order?: number;
}
