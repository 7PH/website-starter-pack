<script setup lang="ts">
const { t } = useI18n();
</script>

<template>
    <div class="min-h-screen flex">
        <!-- Left panel - Branding (hidden on mobile) -->
        <div
            class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white p-12 flex-col justify-between"
        >
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
        <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-surface-50 dark:bg-surface-900">
            <!-- Mobile header -->
            <div class="lg:hidden absolute top-0 left-0 right-0 p-4">
                <NuxtLink to="/" class="text-xl font-bold text-primary">
                    {{ t('core.app.name') }}
                </NuxtLink>
            </div>

            <div class="w-full max-w-md">
                <NuxtPage />
            </div>
        </div>
    </div>
</template>
