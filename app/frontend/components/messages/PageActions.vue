<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
const props = defineProps<{
    includeClosed: boolean;
    totalCount: number;
}>();

const emit = defineEmits<{
    'update:includeClosed': [value: boolean];
    newConversation: [];
}>();

const { t } = useI18n();

const includeClosedModel = computed({
    get: () => props.includeClosed,
    set: (value: boolean) => emit('update:includeClosed', value),
});
</script>

<template>
    <div class="page-header">
        <div class="header-left">
            <span class="conversation-count">{{ totalCount }} {{ t('core.messages.conversations') }}</span>
        </div>
        <div class="header-right">
            <UCheckbox v-model="includeClosedModel" :label="t('core.messages.showClosed')" />
            <UButton
                icon="i-lucide-plus"
                :label="t('core.messages.newConversation')"
                @click="$emit('newConversation')"
            />
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.page-header {
    @apply flex items-center justify-between mb-4;
}

.header-left {
    @apply flex items-center gap-4;
}

.conversation-count {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.header-right {
    @apply flex items-center gap-4;
}
</style>
