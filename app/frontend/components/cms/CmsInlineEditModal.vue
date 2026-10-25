<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Quick edit of one field of a CMS page, from the page itself. Saves only that field; the page's data reloads in place.
import { cmsLabel, isEmptyField } from '~/utils/cms';

const props = defineProps<{ page: CmsPageRead; field: string }>();
const open = defineModel<boolean>('open', { required: true });

const { t, locale } = useI18n();
const api = useApi();
const { showSuccess, showWarning } = useToastHelpers();
const showCmsError = useCmsErrorToast();

const isFixed = props.page.fixed_key != null;
const endpoint = isFixed
    ? `/cms/admin/fixed/${encodeURIComponent(props.page.fixed_key!)}`
    : `/cms/admin/pages/${props.page.id}`;
const editorUrl = isFixed ? `/admin/cms/fixed/${props.page.fixed_key}` : `/admin/cms/pages/${props.page.id}`;

const [{ data: current, pending }, { data: templates }] = await Promise.all([
    useAsyncData(`cms-inline-${endpoint}`, () => api.get<CmsPageAdminRead>(endpoint), { server: false }),
    useAsyncData<CmsTemplateRead[]>('cms-templates', () => api.get('/cms/templates'), { server: false }),
]);

// Title and cover of a free page aren't template fields, but edit the same way.
const pageField = (name: string, type: 'text' | 'image', label: string, max: number | null): CmsTemplateField => ({
    name,
    type,
    label: { [locale.value]: label },
    help: {},
    default: '',
    required: type === 'text',
    max,
});
const pageFields: Record<string, CmsTemplateField> = isFixed
    ? {}
    : {
          title: pageField('title', 'text', t('cms.pages.title'), 200),
          cover: pageField('cover', 'image', t('cms.pages.cover'), null),
      };
const ownField = pageFields[props.field];
const fieldDef = computed<CmsTemplateField | undefined>(
    () =>
        ownField ??
        templates.value?.find((tpl) => tpl.name === props.page.template)?.fields.find((f) => f.name === props.field),
);

const value = ref<unknown>(null);
watch(
    current,
    (page) => {
        if (!page) return;
        value.value =
            ownField?.name === 'title'
                ? page.title
                : ownField?.name === 'cover'
                  ? page.cover
                  : page.fields[props.field];
    },
    { immediate: true },
);

const saving = ref(false);
async function save() {
    const field = fieldDef.value;
    if (!field || !current.value) return;
    if (field.required && isEmptyField(field, value.value))
        return showWarning(t('cms.pages.required', { field: cmsLabel(field.label, locale.value) }));
    const media = (value.value as CmsMediaRead | null) ?? null;
    const body =
        ownField?.name === 'title'
            ? { title: value.value }
            : ownField?.name === 'cover'
              ? { cover_media_id: media?.id ?? null }
              : {
                    fields: {
                        [field.name]: field.type === 'image' ? (media ? { media_id: media.id } : null) : value.value,
                    },
                };
    saving.value = true;
    try {
        await api.patch(endpoint, { ...body, updated_at: current.value.updated_at });
        // Lists and blocks built from CMS data (useCmsPageList...) may show this field too. Also reloads this modal's copy.
        await refreshNuxtData();
        showSuccess(t('cms.inline.saved'));
        open.value = false;
    } catch (e) {
        showCmsError(e, { fields: [field], onReload: () => refreshNuxtData() });
    } finally {
        saving.value = false;
    }
}
</script>

<template>
    <UModal v-model:open="open" :title="t('cms.inline.title')" class="sm:max-w-2xl">
        <template #body>
            <div v-if="pending" class="flex justify-center py-8">
                <UIcon name="i-lucide-loader-2" class="animate-spin text-3xl text-primary-500" />
            </div>
            <CmsField v-else-if="fieldDef" v-model="value" :field="fieldDef" />
            <p v-else class="text-sm text-gray-500">{{ t('cms.inline.unknownField') }}</p>
        </template>
        <template #footer>
            <div class="flex w-full flex-wrap items-center justify-between gap-3">
                <ULink :to="editorUrl" class="text-sm text-gray-500 hover:underline">{{
                    t('cms.inline.fullEditor')
                }}</ULink>
                <div class="flex gap-2">
                    <UButton :label="t('cms.inline.cancel')" color="neutral" variant="ghost" @click="open = false" />
                    <UButton
                        :label="t('cms.inline.save')"
                        icon="i-lucide-check"
                        :loading="saving"
                        :disabled="!fieldDef || !current"
                        @click="save"
                    />
                </div>
            </div>
        </template>
    </UModal>
</template>
