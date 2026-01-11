<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import type { AdminNavItem } from '~/config/admin-nav';
import { CORE_ADMIN_NAV } from '~/config/admin-nav';
import { PROJECT_ADMIN_NAV } from '~/config/admin-nav-ext';

const route = useRoute();
const config = useRuntimeConfig();

// Merge core and project nav items, add dynamic items, sorted by order
const navItems = computed(() => {
    const items: AdminNavItem[] = [...CORE_ADMIN_NAV, ...PROJECT_ADMIN_NAV];

    // Add Adminer link if configured
    if (config.public.adminerUrl) {
        items.push({
            label: 'Adminer',
            icon: 'i-lucide-database',
            href: config.public.adminerUrl as string,
            external: true,
            order: 100,
        });
    }

    // Add Umami Analytics link if configured
    if (config.public.umamiDashboardUrl) {
        items.push({
            label: 'Analytics',
            icon: 'i-lucide-bar-chart-3',
            href: config.public.umamiDashboardUrl as string,
            external: true,
            order: 101,
        });
    }

    return items
        .filter((item) => !item.condition || item.condition())
        .sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
});

// Check if a nav item is active
function isActive(to: string | undefined): boolean {
    if (!to) return false;
    if (to === '/admin') {
        return route.path === '/admin';
    }
    return route.path.startsWith(to);
}
</script>

<template>
    <nav class="admin-subnav">
        <template v-for="item in navItems">
            <!-- External link -->
            <a
                v-if="item.external && item.href"
                :key="item.href"
                :href="item.href"
                target="_blank"
                rel="noopener noreferrer"
                class="subnav-btn"
            >
                <UIcon :name="item.icon" />
                <span>{{ item.label }}</span>
                <UIcon name="i-lucide-external-link" class="external-icon" />
            </a>
            <!-- Internal link -->
            <NuxtLink v-else :key="item.to" :to="item.to" class="subnav-btn" :class="{ active: isActive(item.to) }">
                <UIcon :name="item.icon" />
                <span>{{ item.label }}</span>
            </NuxtLink>
        </template>
    </nav>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.admin-subnav {
    @apply flex flex-wrap gap-2;
}

.subnav-btn {
    @apply inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium;
    @apply text-slate-600 dark:text-slate-400 no-underline;
    @apply hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors;
}

.subnav-btn.active {
    @apply bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300;
}

.external-icon {
    @apply text-xs opacity-50;
}
</style>
