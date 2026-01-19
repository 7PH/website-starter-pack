<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
const { t } = useI18n();
const auth = useAuth();

const organizationCount = computed(() => auth.user?.organizations?.length ?? 0);
</script>

<template>
    <div class="space-y-6">
        <UCard>
            <div class="org-link-card">
                <UIcon name="i-lucide-building-2" class="card-icon" />
                <div class="card-content">
                    <h3 class="card-title">{{ t('core.organizations.title') }}</h3>
                    <p class="card-description">
                        {{
                            organizationCount > 0
                                ? t('core.organizations.memberOfCount', { count: organizationCount })
                                : t('core.organizations.noOrganizations')
                        }}
                    </p>
                </div>
                <NuxtLink to="/organizations">
                    <UButton :label="t('core.organizations.manageOrganizations')" icon="i-lucide-arrow-right" />
                </NuxtLink>
            </div>
        </UCard>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.org-link-card {
    @apply flex items-center gap-4;
}

.card-icon {
    @apply text-4xl text-primary-500;
}

.card-content {
    @apply flex-1;
}

.card-title {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100 m-0;
}

.card-description {
    @apply text-sm text-gray-500 dark:text-gray-400 mt-1;
}
</style>
