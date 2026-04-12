<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { useMainNavExtensions } from '~/config/main-nav-ext';

const auth = useAuth();
const navExtensions = useMainNavExtensions();
const accountActions = useAccountActions();
const { t } = useI18n();
const { isPremium, loading: subscriptionLoading } = useStripe();
const { locale, availableLocales, setLocale } = useAppLocale();
const { isDark, toggle: toggleColorMode } = useColorModeToggle();
const config = useRuntimeConfig();
const stripeEnabled = computed(() => String(config.public.stripeEnabled) === 'true');

// User dropdown items
const userMenuItems = computed(() => [
    [{ label: auth.user?.first_name, avatar: { icon: 'i-lucide-user' }, type: 'label' as const }],
    [
        { label: t('core.messages.title'), icon: 'i-lucide-message-square', to: '/messages' },
        ...(config.public.organizationsEnabled
            ? [{ label: t('core.organizations.title'), icon: 'i-lucide-building-2', to: '/organizations' }]
            : []),
        { label: t('core.account.title'), icon: 'i-lucide-settings', to: '/account' },
        ...(auth.user?.is_admin
            ? [{ label: t('core.admin.title'), icon: 'i-lucide-shield', to: '/admin/users', color: 'error' as const }]
            : []),
    ],
    [{ label: t('core.auth.logout'), icon: 'i-lucide-log-out', onSelect: onSelectLogout }],
]);

// Settings dropdown items
const settingsMenuItems = computed(() => [
    [
        {
            label: isDark.value ? t('core.theme.light') : t('core.theme.dark'),
            icon: isDark.value ? 'i-lucide-sun' : 'i-lucide-moon',
            onSelect: toggleColorMode,
        },
    ],
    [...availableLocales.value]
        .sort((a, b) => (a.code === 'en' ? -1 : b.code === 'en' ? 1 : 0))
        .map((l) => ({
            label: l.name,
            icon: l.code === locale.value ? 'i-lucide-check' : 'i-lucide-globe',
            onSelect: () => setLocale(l.code),
        })),
]);

function onSelectLogout() {
    accountActions.logout();
}
</script>

<template>
    <header class="header">
        <!-- Backdrop blur layer -->
        <div class="absolute inset-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md -z-10" />
        <!-- Gradient bottom border -->
        <div
            class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-400 to-transparent dark:via-primary-500/50"
        />

        <div class="header-content page-box">
            <!-- Left: Navigation -->
            <nav class="nav-links">
                <NuxtLink to="/" class="nav-icon-link" aria-label="Home">
                    <UIcon name="i-lucide-home" />
                </NuxtLink>
                <ClientOnly>
                    <NuxtLink v-for="item in navExtensions" :key="item.to" :to="item.to" class="nav-link">
                        <UIcon :name="item.icon" />
                        <span>{{ item.label }}</span>
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
                        <!-- Premium badge or Upgrade CTA (only when Stripe is enabled) -->
                        <NuxtLink
                            v-if="stripeEnabled && !subscriptionLoading"
                            to="/premium"
                            :class="isPremium ? 'premium-badge' : 'upgrade-cta'"
                        >
                            <UIcon name="i-lucide-star" />
                            <span>{{ isPremium ? t('core.billing.premium') : t('core.billing.upgrade') }}</span>
                        </NuxtLink>

                        <!-- User dropdown -->
                        <UDropdownMenu :items="userMenuItems">
                            <UButton
                                :label="auth.user?.first_name"
                                icon="i-lucide-user"
                                color="neutral"
                                variant="ghost"
                                size="sm"
                                trailing-icon="i-lucide-chevron-down"
                            />
                        </UDropdownMenu>

                        <!-- Settings dropdown -->
                        <UDropdownMenu :items="settingsMenuItems">
                            <UButton icon="i-lucide-settings" color="neutral" variant="ghost" size="sm" />
                        </UDropdownMenu>
                    </template>

                    <!-- SSR Placeholder -->
                    <template #fallback>
                        <div class="nav-actions invisible">
                            <span>{{ t('core.auth.login') }}</span>
                            <UButton :label="t('core.auth.register')" size="sm" />
                        </div>
                    </template>
                </ClientOnly>
            </div>
        </div>
    </header>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.header {
    @apply sticky top-0 z-40 relative;
    @apply border-b border-slate-200/50 dark:border-slate-700/50;
    min-height: var(--page-header-height);
}

.header-content {
    @apply flex items-center justify-between h-full;
    min-height: var(--page-header-height);
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

.nav-icon-link {
    @apply flex items-center justify-center w-9 h-9 rounded-lg;
    @apply text-slate-600 dark:text-slate-300;
    @apply hover:bg-slate-100 dark:hover:bg-slate-800/50;
    @apply transition-colors duration-200 no-underline;
}

.nav-icon-link.router-link-active {
    @apply text-primary-600 dark:text-primary-400;
}

.nav-actions {
    @apply flex items-center gap-3;
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
