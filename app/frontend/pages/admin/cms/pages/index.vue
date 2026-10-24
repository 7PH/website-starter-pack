<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
import { cmsLabel } from '~/utils/cms';

definePageMeta({
    middleware: ['admin', 'cms'],
});

const { t, locale } = useI18n();
const api = useApi();
const router = useRouter();
const { showError } = useToastHelpers();

const [{ data, pending }, { data: templates }] = await Promise.all([
    useAsyncData<CmsAdminPagesResponse>('cms-admin-pages', () => api.get('/cms/admin/pages'), { server: false }),
    useAsyncData<CmsTemplateRead[]>('cms-templates', () => api.get('/cms/templates'), { server: false }),
]);

// The site's language, not the browser's: the client reads her admin in it.
const formatDate = (date: string) => new Date(date).toLocaleDateString(locale.value);
const templateLabel = (name: string) =>
    cmsLabel(templates.value?.find((tpl) => tpl.name === name)?.label, locale.value);
const freeTemplates = computed(() =>
    (templates.value ?? [])
        .filter((tpl) => !tpl.fixed)
        .map((tpl) => ({ value: tpl.name, label: cmsLabel(tpl.label, locale.value) })),
);

const createOpen = ref(false);
const creating = ref(false);
const newPage = ref({ title: '', template: 'default' });

function openCreate() {
    newPage.value = { title: '', template: freeTemplates.value[0]?.value ?? 'default' };
    createOpen.value = true;
}

async function create() {
    creating.value = true;
    try {
        const page = await api.post<CmsPageAdminRead>('/cms/admin/pages', newPage.value);
        await router.push(`/admin/cms/pages/${page.id}`);
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        creating.value = false;
    }
}
</script>

<template>
    <div class="page-box">
        <AdminPageBanner />

        <div class="max-w-4xl mx-auto flex flex-col gap-8">
            <div class="flex items-center justify-between gap-4">
                <h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ t('cms.pages.listTitle') }}</h1>
                <UButton :label="t('cms.pages.new')" icon="i-lucide-plus" @click="openCreate" />
            </div>

            <div v-if="pending" class="flex justify-center py-16">
                <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary-500" />
            </div>

            <template v-else-if="data">
                <section v-if="data.fixed.length" class="flex flex-col gap-3">
                    <div>
                        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            {{ t('cms.pages.fixed') }}
                        </h2>
                        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('cms.pages.fixedHelp') }}</p>
                    </div>
                    <UCard :ui="{ body: 'p-0 sm:p-0' }">
                        <ul class="divide-y divide-gray-200 dark:divide-gray-800">
                            <li v-for="item in data.fixed" :key="item.key">
                                <NuxtLink
                                    :to="`/admin/cms/fixed/${item.key}`"
                                    class="flex items-center justify-between gap-4 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                                >
                                    <span class="font-medium text-gray-900 dark:text-gray-100">
                                        {{ templateLabel(item.key) }}
                                    </span>
                                    <span class="text-sm text-gray-500 dark:text-gray-400">
                                        {{
                                            item.updated_at
                                                ? t('cms.pages.editedOn', { date: formatDate(item.updated_at!) })
                                                : t('cms.pages.neverEdited')
                                        }}
                                    </span>
                                </NuxtLink>
                            </li>
                        </ul>
                    </UCard>
                </section>

                <section class="flex flex-col gap-3">
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ t('cms.pages.free') }}</h2>
                    <UCard :ui="{ body: 'p-0 sm:p-0' }">
                        <p v-if="!data.pages.length" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                            {{ t('cms.pages.empty') }}
                        </p>
                        <ul v-else class="divide-y divide-gray-200 dark:divide-gray-800">
                            <li v-for="page in data.pages" :key="page.id">
                                <NuxtLink
                                    :to="`/admin/cms/pages/${page.id}`"
                                    class="flex flex-wrap items-center justify-between gap-2 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                                >
                                    <span class="flex flex-col min-w-0">
                                        <span class="font-medium text-gray-900 dark:text-gray-100 truncate">
                                            {{ page.title }}
                                        </span>
                                        <span class="text-sm text-gray-500 dark:text-gray-400 truncate">
                                            /{{ page.slug }}
                                            <template v-if="freeTemplates.length > 1">
                                                · {{ templateLabel(page.template) }}
                                            </template>
                                        </span>
                                    </span>
                                    <span class="flex items-center gap-2">
                                        <UBadge
                                            :label="
                                                page.published
                                                    ? t('cms.pages.status.published')
                                                    : t('cms.pages.status.draft')
                                            "
                                            :color="page.published ? 'success' : 'neutral'"
                                            variant="subtle"
                                        />
                                        <UBadge
                                            v-if="page.show_in_blog"
                                            :label="t('cms.pages.status.inBlog')"
                                            color="info"
                                            variant="subtle"
                                        />
                                        <span class="text-sm text-gray-500 dark:text-gray-400">
                                            {{ t('cms.pages.editedOn', { date: formatDate(page.updated_at) }) }}
                                        </span>
                                    </span>
                                </NuxtLink>
                            </li>
                        </ul>
                    </UCard>
                </section>
            </template>
        </div>

        <UModal v-model:open="createOpen" :title="t('cms.pages.new')">
            <template #body>
                <form id="cms-new-page" class="flex flex-col gap-4" @submit.prevent="create">
                    <UFormField :label="t('cms.pages.title')" :help="t('cms.pages.newHelp')" required>
                        <UInput v-model="newPage.title" :maxlength="200" class="w-full" autofocus />
                    </UFormField>
                    <UFormField v-if="freeTemplates.length > 1" :label="t('cms.pages.template')">
                        <USelect v-model="newPage.template" :items="freeTemplates" class="w-full" />
                    </UFormField>
                </form>
            </template>
            <template #footer>
                <div class="flex justify-end gap-2 w-full">
                    <UButton
                        :label="t('core.common.cancel')"
                        color="neutral"
                        variant="ghost"
                        @click="createOpen = false"
                    />
                    <UButton
                        type="submit"
                        form="cms-new-page"
                        :label="t('cms.pages.create')"
                        :loading="creating"
                        :disabled="!newPage.title.trim()"
                    />
                </div>
            </template>
        </UModal>
    </div>
</template>
