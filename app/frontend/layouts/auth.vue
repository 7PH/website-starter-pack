<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
const { t } = useI18n();
const { uiLocale } = useAppLocale();
</script>

<template>
    <UApp :locale="uiLocale">
        <div class="min-h-screen flex">
            <!-- Left panel - Branding (hidden on mobile) -->
            <div class="auth-brand-panel">
                <div>
                    <NuxtLink to="/" class="text-2xl font-bold">
                        {{ t('core.app.name') }}
                    </NuxtLink>
                </div>

                <div class="space-y-6">
                    <h1 class="text-4xl font-bold">
                        {{ t('core.auth.welcomeBack') }}
                    </h1>
                    <p class="text-lg text-white/80">
                        {{ t('core.auth.brandingTagline') }}
                    </p>
                </div>

                <div class="text-sm text-white/60">&copy; {{ new Date().getFullYear() }} {{ t('core.app.name') }}</div>
            </div>

            <!-- Right panel - Form -->
            <!-- A column, not absolute positioning: on short screens (phones, 200% zoom) the logo pushes the form down instead of overlapping it -->
            <div class="w-full lg:w-1/2 flex flex-col p-8 bg-surface-50 dark:bg-surface-900">
                <!-- Mobile header -->
                <div class="lg:hidden mb-6">
                    <NuxtLink to="/" class="text-xl font-bold text-primary">
                        {{ t('core.app.name') }}
                    </NuxtLink>
                </div>

                <main id="main-content" tabindex="-1" class="w-full max-w-md m-auto outline-none">
                    <NuxtPage />
                </main>
            </div>
        </div>
    </UApp>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.auth-brand-panel {
    @apply hidden lg:flex lg:w-1/2 text-white p-12 flex-col justify-between;
    background: var(--gradient-brand);
}
</style>
