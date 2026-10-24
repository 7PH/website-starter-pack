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

// One section per free template, pages in the order she set (it drives lists like "every service").
const groups = computed(() => {
    const pages = data.value?.pages ?? [];
    return [...new Set(pages.map((p) => p.template))].map((name) => ({
        name,
        pages: pages.filter((p) => p.template === name),
    }));
});

async function saveOrder(template: string) {
    const ids = (data.value?.pages ?? []).filter((p) => p.template === template).map((p) => p.id);
    try {
        await api.put('/cms/admin/pages/order', { ids });
    } catch (error) {
        showError(error, 'core.errors.generic');
        await refreshNuxtData('cms-admin-pages');
    }
}

// Moves a page to another one's place within its template, in the local list (saved by the caller).
function place(page: CmsPageListItem, target: CmsPageListItem) {
    if (!data.value || page.template !== target.template || page.id === target.id) return false;
    const pages = [...data.value.pages];
    const from = pages.findIndex((p) => p.id === page.id);
    const to = pages.findIndex((p) => p.id === target.id);
    if (from < 0 || to < 0) return false;
    pages.splice(to, 0, pages.splice(from, 1)[0]!);
    data.value = { ...data.value, pages };
    return true;
}

function move(pages: CmsPageListItem[], index: number, delta: number) {
    if (place(pages[index]!, pages[index + delta]!)) saveOrder(pages[index]!.template);
}

// Drag and drop for mouse users. The arrows stay for touch screens and keyboards, which native drag doesn't serve.
const dragged = shallowRef<CmsPageListItem | null>(null);
const dragMoved = ref(false);
function onDragEnter(target: CmsPageListItem) {
    if (dragged.value && place(dragged.value, target)) dragMoved.value = true;
}
function onDragEnd() {
    if (dragged.value && dragMoved.value) saveOrder(dragged.value.template);
    dragged.value = null;
    dragMoved.value = false;
}

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

                <section v-if="!groups.length" class="flex flex-col gap-3">
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ t('cms.pages.free') }}</h2>
                    <UCard>
                        <p class="py-4 text-center text-gray-500 dark:text-gray-400">{{ t('cms.pages.empty') }}</p>
                    </UCard>
                </section>
                <section v-for="group in groups" :key="group.name" class="flex flex-col gap-3">
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {{
                            groups.length > 1 || freeTemplates.length > 1
                                ? templateLabel(group.name) || group.name
                                : t('cms.pages.free')
                        }}
                    </h2>
                    <UCard :ui="{ body: 'p-0 sm:p-0' }">
                        <ul class="divide-y divide-gray-200 dark:divide-gray-800">
                            <li
                                v-for="(page, index) in group.pages"
                                :key="page.id"
                                class="flex items-center"
                                :class="{ 'opacity-50': dragged?.id === page.id }"
                                :draggable="group.pages.length > 1"
                                @dragstart="dragged = page"
                                @dragenter="onDragEnter(page)"
                                @dragover.prevent
                                @dragend="onDragEnd"
                            >
                                <UIcon
                                    v-if="group.pages.length > 1"
                                    name="i-lucide-grip-vertical"
                                    class="ml-2 shrink-0 cursor-grab text-gray-400"
                                    :aria-hidden="true"
                                />
                                <NuxtLink
                                    draggable="false"
                                    :to="`/admin/cms/pages/${page.id}`"
                                    class="flex flex-1 min-w-0 flex-wrap items-center justify-between gap-2 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                                >
                                    <span class="flex flex-col min-w-0">
                                        <span class="font-medium text-gray-900 dark:text-gray-100 truncate">
                                            {{ page.title }}
                                        </span>
                                        <span class="text-sm text-gray-500 dark:text-gray-400 truncate">
                                            /{{ page.slug }}
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
                                <div v-if="group.pages.length > 1" class="flex flex-col pr-2">
                                    <UButton
                                        icon="i-lucide-chevron-up"
                                        :aria-label="t('cms.pages.moveUp')"
                                        color="neutral"
                                        variant="ghost"
                                        size="xs"
                                        :disabled="index === 0"
                                        @click="move(group.pages, index, -1)"
                                    />
                                    <UButton
                                        icon="i-lucide-chevron-down"
                                        :aria-label="t('cms.pages.moveDown')"
                                        color="neutral"
                                        variant="ghost"
                                        size="xs"
                                        :disabled="index === group.pages.length - 1"
                                        @click="move(group.pages, index, 1)"
                                    />
                                </div>
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
