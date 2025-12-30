<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { CORE_ADMIN_NAV } from '~/config/admin-nav';
import { PROJECT_ADMIN_NAV } from '~/config/admin-nav-ext';

const route = useRoute();

// Merge core and project nav items, sorted by order
const navItems = computed(() => {
    return [...CORE_ADMIN_NAV, ...PROJECT_ADMIN_NAV].sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
});

// Check if a nav item is active
function isActive(to: string): boolean {
    if (to === '/admin') {
        return route.path === '/admin';
    }
    return route.path.startsWith(to);
}
</script>

<template>
    <nav class="admin-nav">
        <ul class="nav-list">
            <li v-for="item in navItems" :key="item.to">
                <NuxtLink :to="item.to" class="nav-link" :class="{ active: isActive(item.to) }">
                    <UIcon :name="item.icon" class="nav-icon" />
                    <span>{{ item.label }}</span>
                </NuxtLink>
            </li>
        </ul>
    </nav>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.admin-nav {
    @apply p-2 flex-1;
}

.nav-list {
    @apply list-none p-0 m-0 flex flex-col gap-1;
}

.nav-link {
    @apply flex items-center gap-3 py-3 px-4 rounded-lg;
    @apply text-gray-600 dark:text-gray-400 no-underline text-sm font-medium;
    @apply transition-all duration-200;
    @apply border-l-4 border-transparent;
}

.nav-link:hover {
    @apply bg-gray-100 dark:bg-gray-700/50 text-gray-900 dark:text-gray-100;
}

.nav-link.active {
    @apply bg-primary-50 dark:bg-primary-900/30;
    @apply text-primary-600 dark:text-primary-300;
    @apply border-l-primary-500;
}

.nav-link.active .nav-icon {
    @apply text-primary-500;
}

.nav-icon {
    @apply text-lg w-5 h-5;
}
</style>
