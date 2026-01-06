<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
const { t } = useI18n();

const currentYear = new Date().getFullYear();
</script>

<template>
    <footer class="page-footer">
        <div class="footer-content">
            <div class="footer-copyright">
                &copy; {{ currentYear }} {{ t('core.app.name') }}. {{ t('core.footer.copyright') }}
            </div>
            <nav class="footer-links">
                <NuxtLink to="/legal/terms" class="footer-link">
                    {{ t('core.legal.terms') }}
                </NuxtLink>
                <span class="footer-separator">·</span>
                <NuxtLink to="/legal/privacy" class="footer-link">
                    {{ t('core.legal.privacy') }}
                </NuxtLink>
                <span class="footer-separator">·</span>
                <NuxtLink to="/legal/cookies" class="footer-link">
                    {{ t('core.legal.cookies') }}
                </NuxtLink>
            </nav>
        </div>
    </footer>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.page-footer {
    @apply py-6 px-4 mt-auto;
    @apply border-t border-gray-200 dark:border-gray-800;
    @apply bg-white dark:bg-transparent;
}

.footer-content {
    @apply max-w-7xl mx-auto;
    @apply flex flex-col sm:flex-row items-center justify-between gap-4;
}

.footer-copyright {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.footer-links {
    @apply flex items-center gap-2;
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
