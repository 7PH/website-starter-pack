<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Wraps a piece of a CMS page so people who can edit it get a pencil opening a quick-edit modal. Visitors get the slot only.
// `field` is a template field name, or 'title' for the title of a free page.
defineProps<{ page: CmsPageRead | null | undefined; field: string }>();

const { t } = useI18n();
const { canEdit } = useCmsAccess();
const open = ref(false);
</script>

<template>
    <div class="relative group/cms">
        <slot />
        <!-- Client only: edit rights are known in the browser, and visitors' HTML must stay untouched. -->
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
        </ClientOnly>
    </div>
</template>
