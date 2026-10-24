<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Floating shortcut to the full editor of the page being viewed, for people who can edit it.
const props = defineProps<{ page: CmsPageRead | null | undefined }>();

const { t } = useI18n();
const { canEdit } = useCmsAccess();
const editorUrl = computed(() => {
    if (!props.page) return null;
    return props.page.fixed_key != null
        ? `/admin/cms/fixed/${props.page.fixed_key}`
        : `/admin/cms/pages/${props.page.id}`;
});
</script>

<template>
    <ClientOnly>
        <UButton
            v-if="canEdit && editorUrl"
            :to="editorUrl"
            :label="t('cms.inline.editPage')"
            icon="i-lucide-pencil"
            class="fixed bottom-16 left-4 z-40 rounded-full shadow-lg"
        />
    </ClientOnly>
</template>
