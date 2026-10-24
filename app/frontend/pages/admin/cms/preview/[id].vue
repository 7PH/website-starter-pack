<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Shows a free page as visitors will see it, drafts included, with the editor's unsaved changes when it has any.
import CmsPageContentDefault from '~/components/cms/CmsPageContent.vue';
import { cmsDraftKey } from '~/utils/cms';
import { getErrorStatus } from '~/utils/errors';

definePageMeta({
    middleware: ['admin', 'cms'],
});

const { t } = useI18n();
const route = useRoute();
const id = Number(route.params.id);
if (!Number.isInteger(id)) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true });
}
const api = useApi();
const draftKey = cmsDraftKey(id);

function readDraft(): CmsPageUpdate | null {
    try {
        const raw = localStorage.getItem(draftKey);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

const hasDraft = ref(false);
const {
    data: page,
    pending,
    error,
    refresh,
} = await useAsyncData<CmsPageAdminRead | null>(
    `cms-preview-${id}`,
    () => {
        const draft = readDraft();
        hasDraft.value = !!draft;
        const request = draft
            ? api.post<CmsPageAdminRead>(`/cms/admin/pages/${id}/preview`, draft)
            : api.get<CmsPageAdminRead>(`/cms/admin/pages/${id}`);
        return request.catch((e) => {
            if (getErrorStatus(e) === 404) return null;
            throw e;
        });
    },
    { server: false },
);

// The editor rewrites the draft on every change: follow it, without a request per keystroke.
const refreshSoon = useDebounceFn(() => refresh(), 400);
useEventListener('storage', (event: StorageEvent) => {
    if (event.key === draftKey) refreshSoon();
});

const PageContent = useOverridable('CmsPageContent', CmsPageContentDefault);

useSeoMeta({ robots: 'noindex' });
</script>

<template>
    <div>
        <div
            v-if="page"
            class="flex flex-wrap items-center justify-center gap-3 px-4 py-2 text-sm bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
        >
            <span>
                {{
                    hasDraft
                        ? t('cms.pages.previewUnsaved')
                        : !page.published
                          ? t('cms.pages.previewDraft')
                          : t('cms.pages.previewBanner')
                }}
            </span>
            <NuxtLink :to="`/admin/cms/pages/${id}`" class="font-medium underline">
                {{ t('cms.pages.backToEditor') }}
            </NuxtLink>
        </div>
        <UAlert
            v-if="!pending && (error || !page)"
            color="error"
            variant="subtle"
            icon="i-lucide-file-x"
            :title="error ? t('cms.pages.loadError') : t('cms.pages.notFound')"
            class="max-w-3xl mx-auto mt-8"
        />
        <component :is="PageContent" v-else-if="page" :page="page" />
    </div>
</template>
