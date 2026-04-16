<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
defineProps<{
    canCreateOrg: boolean;
}>();

defineEmits<{
    create: [];
}>();

const { t } = useI18n();
</script>

<template>
    <div class="content-header">
        <UButton
            v-if="canCreateOrg"
            :label="t('core.organizations.createOrganization')"
            icon="i-lucide-plus"
            @click="$emit('create')"
        />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.content-header {
    @apply flex justify-end mb-6;
}
</style>
