<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Edit one photo: description, focal point (with crop previews) and delete. */
const props = defineProps<{ media: CmsMediaRead }>();
const emit = defineEmits<{ updated: [media: CmsMediaRead]; deleted: [id: number] }>();

const { t, locale } = useI18n();
const api = useApi();
const modal = useModalStore();
const { showSuccess, showError } = useToastHelpers();

const ALT_MAX = 300;
const alt = ref('');
const focalX = ref(0.5);
const focalY = ref(0.5);
const saving = ref(false);
const deleting = ref(false);
// Pages that stopped the last delete, shown with links to their editor.
const usedBy = ref<CmsMediaUsage[]>([]);

watch(
    () => props.media,
    (media) => {
        alt.value = media.alt;
        focalX.value = media.focal_x;
        focalY.value = media.focal_y;
        usedBy.value = [];
    },
    { immediate: true },
);

const dirty = computed(
    () =>
        alt.value.trim() !== props.media.alt ||
        focalX.value !== props.media.focal_x ||
        focalY.value !== props.media.focal_y,
);
// Crop previews follow the marker before saving.
const preview = computed(() => ({ ...props.media, focal_x: focalX.value, focal_y: focalY.value }));
const addedOn = computed(() => new Date(props.media.created_at).toLocaleDateString(locale.value));

/** Resolves true once saved, so the page can save before closing the panel. */
async function save(): Promise<boolean> {
    saving.value = true;
    try {
        const media = await api.patch<CmsMediaRead>(`/cms/media/${props.media.id}`, {
            alt: alt.value.trim(),
            focal_x: focalX.value,
            focal_y: focalY.value,
        });
        emit('updated', media);
        showSuccess(t('cms.media.saved'));
        return true;
    } catch (error) {
        showError(error, 'core.errors.generic');
        return false;
    } finally {
        saving.value = false;
    }
}

defineExpose({ dirty, save });

const pageLink = (page: CmsMediaUsage) =>
    page.fixed_key ? `/admin/cms/fixed/${page.fixed_key}` : `/admin/cms/pages/${page.id}`;

async function remove() {
    const confirmed = await modal.open<boolean>('confirm', {
        title: t('cms.media.deleteTitle'),
        message: t('cms.media.deleteMessage'),
        confirmText: t('cms.media.delete'),
        confirmColor: 'error',
        icon: 'i-lucide-trash-2',
    });
    if (!confirmed) return;
    deleting.value = true;
    try {
        usedBy.value = await deleteCmsMedia(props.media.id);
        if (usedBy.value.length) return;
        emit('deleted', props.media.id);
        showSuccess(t('cms.media.deleted'));
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        deleting.value = false;
    }
}
</script>

<template>
    <div class="flex flex-col gap-6">
        <section class="flex flex-col gap-2">
            <h3 class="font-medium text-gray-900 dark:text-gray-100">{{ t('cms.media.focal') }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('cms.media.focalHelp') }}</p>
            <CmsFocalPicker v-model:x="focalX" v-model:y="focalY" :media="media" />
            <div class="flex items-end gap-3">
                <figure class="w-24 shrink-0">
                    <CmsImage :media="preview" sizes="96px" class="aspect-square w-full rounded object-cover" />
                    <figcaption class="mt-1 text-xs text-gray-500">{{ t('cms.media.previewSquare') }}</figcaption>
                </figure>
                <figure class="min-w-0 flex-1">
                    <CmsImage :media="preview" sizes="320px" class="aspect-[21/9] w-full rounded object-cover" />
                    <figcaption class="mt-1 text-xs text-gray-500">{{ t('cms.media.previewWide') }}</figcaption>
                </figure>
            </div>
        </section>

        <UFormField :label="t('cms.media.alt')" :help="t('cms.media.altHelp')">
            <UTextarea v-model="alt" :maxlength="ALT_MAX" :rows="2" autoresize class="w-full" />
            <template #hint>
                <span class="text-xs text-gray-500">{{ alt.length }}/{{ ALT_MAX }}</span>
            </template>
        </UFormField>

        <p class="text-xs break-all text-gray-500 dark:text-gray-400">
            {{ media.original_name }}<br />
            {{ t('cms.media.info', { width: media.width, height: media.height, date: addedOn }) }}
        </p>

        <UAlert
            v-if="usedBy.length"
            color="warning"
            variant="subtle"
            icon="i-lucide-triangle-alert"
            :title="t('cms.media.inUseTitle')"
        >
            <template #description>
                <p>{{ t('cms.media.inUse') }}</p>
                <ul class="mt-1 list-disc pl-5">
                    <li v-for="page in usedBy" :key="page.id">
                        <NuxtLink :to="pageLink(page)" class="underline">{{ page.title }}</NuxtLink>
                    </li>
                </ul>
            </template>
        </UAlert>

        <div class="flex items-center justify-between gap-3">
            <UButton
                :label="t('cms.media.delete')"
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                :loading="deleting"
                @click="remove"
            />
            <UButton :label="t('cms.media.save')" :disabled="!dirty" :loading="saving" @click="save" />
        </div>
    </div>
</template>
