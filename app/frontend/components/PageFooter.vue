<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
const { t } = useI18n();

const currentYear = new Date().getFullYear();

const legalLinks = computed(() => [
    { to: '/legal/terms', label: t('core.legal.terms') },
    { to: '/legal/privacy', label: t('core.legal.privacy') },
    { to: '/legal/cookies', label: t('core.legal.cookies') },
]);
</script>

<template>
    <footer class="page-footer">
        <div class="footer-content">
            <div class="footer-copyright">
                &copy; {{ currentYear }} {{ t('core.app.name')
                }}<span class="max-sm:hidden">. {{ t('core.footer.copyright') }}</span>
            </div>
            <nav class="footer-links">
                <span v-for="(link, i) in legalLinks" :key="link.to" class="flex items-center gap-2">
                    <span v-if="i" class="footer-separator">·</span>
                    <NuxtLink :to="link.to" class="footer-link">{{ link.label }}</NuxtLink>
                </span>
            </nav>
            <!-- Phones: one link instead of three, so the footer stays a single short line. -->
            <div class="footer-legal-compact">
                <UPopover>
                    <button type="button" class="footer-link">{{ t('core.legal.title') }}</button>
                    <template #content>
                        <nav class="flex flex-col p-1">
                            <NuxtLink
                                v-for="link in legalLinks"
                                :key="link.to"
                                :to="link.to"
                                class="footer-link px-3 py-2"
                            >
                                {{ link.label }}
                            </NuxtLink>
                        </nav>
                    </template>
                </UPopover>
            </div>
        </div>
    </footer>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.page-footer {
    @apply relative z-10 py-3 px-4 mt-auto;
    @apply border-t border-gray-200 dark:border-gray-800;
    @apply bg-white dark:bg-slate-900;
}

.footer-content {
    @apply max-w-7xl mx-auto;
    @apply flex items-center justify-between gap-4;
}

.footer-copyright {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.footer-links {
    @apply flex items-center gap-2 max-sm:hidden;
}

.footer-legal-compact {
    @apply sm:hidden;
}

.footer-link {
    @apply text-sm text-gray-500 dark:text-gray-400;
    @apply hover:text-primary-600 dark:hover:text-primary-400;
    @apply no-underline transition-colors;
}

.footer-separator {
    @apply text-gray-300 dark:text-gray-600;
}
</style>
