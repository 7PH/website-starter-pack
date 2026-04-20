<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
const { t } = useI18n();

const props = defineProps<{
    organization: UserOrganizationInfo;
    isLeaving?: boolean;
}>();

const emit = defineEmits<{
    leave: [];
}>();

const isAdmin = computed(() => props.organization.is_admin);
const orgLink = computed(() => `/organizations/${props.organization.organization_id}`);

function handleLeave(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    emit('leave');
}
</script>

<template>
    <NuxtLink :to="orgLink" class="block">
        <UiHoverCard class="org-card group cursor-pointer">
            <div class="card-header" :class="isAdmin ? 'header-admin' : 'header-member'">
                <UIcon name="i-lucide-building-2" class="text-lg opacity-70" />
                <UBadge
                    :label="isAdmin ? t('core.organizations.admin') : t('core.organizations.member')"
                    :color="isAdmin ? 'info' : 'neutral'"
                    size="xs"
                />
            </div>

            <div class="card-content">
                <h3 class="card-title group-hover:text-primary-500">
                    {{ organization.organization_name }}
                </h3>
            </div>

            <div class="card-footer">
                <UButton
                    :label="t('core.organizations.leave')"
                    color="error"
                    variant="ghost"
                    size="xs"
                    :loading="isLeaving"
                    @click="handleLeave"
                />
            </div>
        </UiHoverCard>
    </NuxtLink>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.org-card {
    @apply flex flex-col overflow-hidden;
}

.card-header {
    @apply flex items-center justify-between px-4 h-12;
}

.header-admin {
    @apply bg-primary-100 dark:bg-primary-900/30;
}

.header-member {
    @apply bg-gray-100 dark:bg-gray-700;
}

.card-content {
    @apply flex-1 px-4 py-4;
}

.card-title {
    @apply font-semibold text-gray-900 dark:text-gray-100 text-base transition-colors;
}

.card-footer {
    @apply flex items-center gap-2 px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700;
}
</style>
