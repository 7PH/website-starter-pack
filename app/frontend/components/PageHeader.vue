<script lang="ts" setup>
const auth = useAuth();
const authActions = useAuthActions();
const { t } = useI18n();
const { isPremium, loading: subscriptionLoading } = useSubscription();
const { locale, availableLocales, setLocale } = useAppLocale();
const { isDark, toggle: toggleColorMode } = useColorModeToggle();

// Language switcher items for UDropdownMenu
const localeMenuItems = computed(() => [
    availableLocales.value.map((l) => ({
        label: l.name,
        onSelect: () => setLocale(l.code),
    })),
]);

function onSelectLogout() {
    authActions.logout();
}
</script>

<template>
    <header class="navbar">
        <!-- Left: Navigation -->
        <nav class="nav-links">
            <NuxtLink to="/" class="nav-link">
                <UIcon name="i-lucide-home" />
                <span>Home</span>
            </NuxtLink>
            <ClientOnly>
                <NuxtLink v-if="auth.user?.is_admin" to="/admin/users" class="nav-link">
                    <UIcon name="i-lucide-settings" />
                    <span>Admin</span>
                </NuxtLink>
            </ClientOnly>
        </nav>

        <!-- Right: Actions -->
        <div class="nav-actions">
            <ClientOnly>
                <!-- Logged out state -->
                <template v-if="!auth.isLoggedIn">
                    <NuxtLink to="/login" class="nav-link">
                        {{ t('core.auth.login') }}
                    </NuxtLink>
                    <NuxtLink to="/login?mode=signup">
                        <UButton :label="t('core.auth.register')" size="sm" />
                    </NuxtLink>
                </template>

                <!-- Logged in state -->
                <template v-else>
                    <!-- Premium badge or Upgrade CTA -->
                    <NuxtLink
                        v-if="!subscriptionLoading"
                        to="/premium"
                        :class="isPremium ? 'premium-badge' : 'upgrade-cta'"
                    >
                        <UIcon name="i-lucide-star" />
                        <span>{{ isPremium ? t('core.billing.premium') : t('core.billing.upgrade') }}</span>
                    </NuxtLink>

                    <span class="nav-user">{{ auth.user?.first_name }}</span>

                    <UButton
                        icon="i-lucide-log-out"
                        color="neutral"
                        variant="ghost"
                        size="sm"
                        aria-label="Logout"
                        @click="onSelectLogout"
                    />
                </template>

                <!-- Theme Toggle -->
                <UButton
                    :icon="isDark ? 'i-lucide-sun' : 'i-lucide-moon'"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    aria-label="Toggle dark mode"
                    @click="toggleColorMode"
                />

                <!-- Language Switcher -->
                <UDropdownMenu :items="localeMenuItems">
                    <UButton color="neutral" variant="ghost" size="sm">
                        {{ locale.toUpperCase() }}
                    </UButton>
                </UDropdownMenu>

                <!-- SSR Placeholder -->
                <template #fallback>
                    <div class="nav-actions invisible">
                        <span>Login</span>
                        <UButton label="Register" size="sm" />
                    </div>
                </template>
            </ClientOnly>
        </div>
    </header>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.navbar {
    @apply flex items-center justify-between px-6 py-3;
    @apply bg-white dark:bg-transparent;
    @apply border-b border-slate-200 dark:border-primary-500;
}

.nav-links {
    @apply flex items-center gap-1;
}

.nav-link {
    @apply flex items-center gap-2 px-3 py-2 rounded-lg;
    @apply text-sm font-medium text-slate-600 dark:text-slate-300;
    @apply hover:bg-slate-100 dark:hover:bg-slate-800/50;
    @apply transition-colors duration-200 no-underline;
}

.nav-link.router-link-active {
    @apply text-primary-600 dark:text-primary-400;
}

.nav-actions {
    @apply flex items-center gap-3;
}

.nav-user {
    @apply text-sm text-slate-600 dark:text-slate-300;
}

.nav-icon-btn {
    @apply flex items-center justify-center w-9 h-9 rounded-lg;
    @apply text-slate-500 dark:text-slate-400;
    @apply hover:bg-slate-100 dark:hover:bg-slate-800/50;
    @apply transition-colors duration-200 cursor-pointer;
    @apply border-none bg-transparent text-sm font-medium;
}

/* Premium badge - amber/gold */
.premium-badge {
    @apply flex items-center gap-1.5 px-3 py-1.5 rounded-full;
    @apply text-xs font-semibold no-underline;
    @apply bg-gradient-to-r from-amber-100 to-amber-200 text-amber-800;
    @apply dark:from-amber-900/50 dark:to-amber-800/50 dark:text-amber-300;
    @apply transition-all duration-200;
}

.premium-badge:hover {
    @apply from-amber-200 to-amber-300 dark:from-amber-800/50 dark:to-amber-700/50;
}

/* Upgrade CTA - primary color */
.upgrade-cta {
    @apply flex items-center gap-1.5 px-3 py-1.5 rounded-full;
    @apply text-xs font-semibold no-underline;
    @apply bg-gradient-to-r from-primary-100 to-primary-200 text-primary-700;
    @apply dark:from-primary-900/50 dark:to-primary-800/50 dark:text-primary-300;
    @apply transition-all duration-200;
}

.upgrade-cta:hover {
    @apply from-primary-200 to-primary-300 dark:from-primary-800/50 dark:to-primary-700/50;
}
</style>
