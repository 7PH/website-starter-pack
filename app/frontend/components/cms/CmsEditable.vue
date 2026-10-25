<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Wraps a piece of a CMS page so people who can edit it get a pencil opening a quick-edit modal. Visitors get the slot only.
// `field` is a template field name, or 'title' for the title of a free page.
// For an empty field, pass `addLabel` instead of a slot: editors get an add button, visitors nothing at all.
defineProps<{ page: CmsPageRead | null | undefined; field: string; addLabel?: string }>();

const { t } = useI18n();
const canEdit = useCmsEditInPlace();
const open = ref(false);
</script>

<template>
    <!-- Client only: edit rights are known in the browser, and visitors' HTML must stay untouched. Empty fallbacks: no placeholder <span> either. -->
    <ClientOnly v-if="addLabel">
        <div v-if="canEdit && page">
            <UButton :label="addLabel" icon="i-lucide-plus" color="neutral" variant="outline" @click="open = true" />
            <LazyCmsInlineEditModal v-if="open" v-model:open="open" :page="page" :field="field" />
        </div>
        <template #fallback />
    </ClientOnly>
    <div v-else class="relative group/cms">
        <slot />
        <ClientOnly>
            <template v-if="canEdit && page">
                <div
                    class="pointer-events-none absolute -inset-1 rounded outline-2 outline-dashed outline-primary-400/70 opacity-0 transition-opacity group-hover/cms:opacity-100"
                />
                <UButton
                    icon="i-lucide-pencil"
                    size="sm"
                    color="primary"
                    :aria-label="t('cms.inline.edit')"
                    class="absolute -top-3 -right-3 z-10 rounded-full shadow opacity-0 transition-opacity group-hover/cms:opacity-100 focus-visible:opacity-100 [@media(hover:none)]:opacity-100"
                    @click="open = true"
                />
                <LazyCmsInlineEditModal v-if="open" v-model:open="open" :page="page" :field="field" />
            </template>
            <template #fallback />
        </ClientOnly>
    </div>
</template>
