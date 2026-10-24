<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
import { cmsLabel } from '~/utils/cms';

const props = defineProps<{ field: CmsTemplateField }>();
const value = defineModel<unknown>();

const { locale } = useI18n();

const text = computed({
    get: () => (typeof value.value === 'string' ? value.value : ''),
    set: (v: string) => (value.value = v),
});
const media = computed({
    get: () => (value.value as CmsMediaRead | null) ?? null,
    set: (v: CmsMediaRead | null) => (value.value = v),
});
const counter = computed(() => (props.field.max ? `${text.value.length} / ${props.field.max}` : undefined));
</script>

<template>
    <UFormField
        :label="cmsLabel(field.label, locale)"
        :description="cmsLabel(field.help, locale)"
        :hint="counter"
        :required="field.required"
    >
        <UInput v-if="field.type === 'text'" v-model="text" :maxlength="field.max ?? undefined" class="w-full" />
        <UTextarea
            v-else-if="field.type === 'textarea'"
            v-model="text"
            :maxlength="field.max ?? undefined"
            :rows="4"
            autoresize
            class="w-full"
        />
        <LazyCmsRichTextEditor v-else-if="field.type === 'richtext'" v-model="text" />
        <CmsImageInput v-else-if="field.type === 'image'" v-model="media" />
    </UFormField>
</template>
