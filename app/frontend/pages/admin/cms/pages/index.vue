<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
import { cmsLabel } from '~/utils/cms';

definePageMeta({
    middleware: ['admin', 'cms'],
});

const { t, locale } = useI18n();
const api = useApi();
const router = useRouter();
const showCmsError = useCmsErrorToast();

const [{ data, pending }, { data: templates }] = await Promise.all([
    useAsyncData<CmsAdminPagesResponse>('cms-admin-pages', () => api.get('/cms/admin/pages'), { server: false }),
    useAsyncData<CmsTemplateRead[]>('cms-templates', () => api.get('/cms/templates'), { server: false }),
]);

// The site's language, not the browser's: the editor reads the admin in it.
const formatDate = (date: string) => new Date(date).toLocaleDateString(locale.value);
const templateLabel = (name: string) =>
    cmsLabel(templates.value?.find((tpl) => tpl.name === name)?.label, locale.value);
const freeTemplates = computed(() =>
    (templates.value ?? [])
        .filter((tpl) => !tpl.fixed)
        .map((tpl) => ({ value: tpl.name, label: cmsLabel(tpl.label, locale.value) })),
);

type Segment = 'all' | 'published' | 'drafts';
const segment = ref<Segment>('all');
const matches = (page: CmsPageListItem) =>
    segment.value === 'all' || page.published === (segment.value === 'published');
const segments = computed(() => {
    const pages = data.value?.pages ?? [];
    const published = pages.filter((p) => p.published).length;
    return [
        { value: 'all', label: t('cms.pages.filter.all'), count: pages.length + (data.value?.fixed.length ?? 0) },
        { value: 'published', label: t('cms.pages.filter.published'), count: published },
        { value: 'drafts', label: t('cms.pages.filter.drafts'), count: pages.length - published },
    ];
});
// Moving a page among filtered ones would jump it over hidden pages.
const canReorder = computed(() => segment.value === 'all');

// One section per free template, pages in the order the editor set (it drives lists like "every service").
const groups = computed(() => {
    const pages = data.value?.pages ?? [];
    return [...new Set(pages.map((p) => p.template))]
        .map((name) => ({ name, pages: pages.filter((p) => p.template === name && matches(p)) }))
        .filter((group) => group.pages.length);
});

async function saveOrder(template: string) {
    const ids = (data.value?.pages ?? []).filter((p) => p.template === template).map((p) => p.id);
    try {
        await api.put('/cms/admin/pages/order', { ids });
    } catch (error) {
        showCmsError(error);
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
        showCmsError(error);
    } finally {
        creating.value = false;
    }
}
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader
            :title="t('cms.pages.listTitle')"
            :count="data ? data.pages.length + data.fixed.length : undefined"
            :description="t('cms.pages.listSubtitle')"
        >
            <template #actions>
                <UButton :label="t('cms.pages.new')" icon="i-lucide-plus" size="lg" @click="openCreate" />
            </template>
        </AdminPageHeader>

        <div v-if="pending" class="flex justify-center py-16">
            <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary" />
        </div>

        <template v-else-if="data">
            <AdminToolbar v-if="data.pages.length" v-model:segment="segment" :segments="segments" />

            <AdminCard v-if="data.fixed.length && segment === 'all'" :title="t('cms.pages.fixed')">
                <div v-for="item in data.fixed" :key="item.key" class="flex items-center hover:bg-elevated">
                    <NuxtLink
                        :to="`/admin/cms/fixed/${item.key}`"
                        class="flex min-w-0 flex-1 items-center gap-3 py-3 pl-4.5"
                    >
                        <span
                            class="flex size-8.5 shrink-0 items-center justify-center rounded-[9px] bg-accented/50 text-muted"
                        >
                            <UIcon name="i-lucide-panels-top-left" class="size-4" />
                        </span>
                        <span class="min-w-0 flex-1 truncate text-sm font-bold text-highlighted">
                            {{ templateLabel(item.key) }}
                        </span>
                        <span class="hidden text-[13px] text-muted md:block">
                            {{
                                item.updated_at
                                    ? t('cms.pages.editedOn', { date: formatDate(item.updated_at) })
                                    : t('cms.pages.neverEdited')
                            }}
                        </span>
                    </NuxtLink>
                    <div class="flex items-center gap-0.5 py-3 pr-4.5 pl-3">
                        <UButton
                            :to="`/admin/cms/fixed/${item.key}`"
                            :label="t('cms.pages.edit')"
                            icon="i-lucide-pencil"
                            color="neutral"
                            variant="outline"
                            size="sm"
                            class="hidden md:flex"
                        />
                        <UIcon name="i-lucide-chevron-right" class="size-4 text-dimmed md:hidden" />
                    </div>
                </div>
            </AdminCard>

            <AdminCard v-if="!data.pages.length" :title="t('cms.pages.free')">
                <p class="px-4.5 py-8 text-center text-sm text-muted">{{ t('cms.pages.empty') }}</p>
            </AdminCard>
            <AdminCard v-else-if="!groups.length">
                <p class="px-4.5 py-8 text-center text-sm text-muted">{{ t('cms.pages.noMatch') }}</p>
            </AdminCard>
            <AdminCard
                v-for="group in groups"
                :key="group.name"
                :title="
                    groups.length > 1 || freeTemplates.length > 1
                        ? templateLabel(group.name) || group.name
                        : t('cms.pages.free')
                "
            >
                <div
                    v-for="(page, index) in group.pages"
                    :key="page.id"
                    class="flex items-center hover:bg-elevated"
                    :class="{ 'opacity-50': dragged?.id === page.id }"
                    :draggable="canReorder && group.pages.length > 1"
                    @dragstart="dragged = page"
                    @dragenter="onDragEnter(page)"
                    @dragover.prevent
                    @dragend="onDragEnd"
                >
                    <UIcon
                        v-if="canReorder && group.pages.length > 1"
                        name="i-lucide-grip-vertical"
                        class="ml-1.5 hidden shrink-0 cursor-grab text-dimmed md:block"
                        :aria-hidden="true"
                    />
                    <NuxtLink
                        draggable="false"
                        :to="`/admin/cms/pages/${page.id}`"
                        class="grid min-w-0 flex-1 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-3 pl-4.5 md:grid-cols-[minmax(0,2.4fr)_110px_minmax(0,1.2fr)]"
                    >
                        <span class="flex min-w-0 items-center gap-3">
                            <span
                                class="flex size-8.5 shrink-0 items-center justify-center rounded-[9px] bg-accented/50 text-muted"
                            >
                                <UIcon name="i-lucide-file-text" class="size-4" />
                            </span>
                            <span class="flex min-w-0 flex-col">
                                <span class="truncate text-sm font-bold text-highlighted">{{ page.title }}</span>
                                <span class="truncate font-mono text-xs text-muted">/{{ page.slug }}</span>
                            </span>
                        </span>
                        <span>
                            <UBadge
                                :label="page.published ? t('cms.pages.status.published') : t('cms.pages.status.draft')"
                                :color="page.published ? 'success' : 'neutral'"
                                variant="soft"
                                class="rounded-full"
                            >
                                <template #leading>
                                    <span class="size-1.5 rounded-full bg-current" />
                                </template>
                            </UBadge>
                        </span>
                        <span class="hidden truncate text-[13px] text-muted md:block">
                            {{ t('cms.pages.editedOn', { date: formatDate(page.updated_at) }) }}
                        </span>
                    </NuxtLink>
                    <div class="flex items-center gap-0.5 py-3 pr-4.5 pl-3">
                        <UButton
                            :to="`/admin/cms/pages/${page.id}`"
                            :label="t('cms.pages.edit')"
                            icon="i-lucide-pencil"
                            color="neutral"
                            variant="outline"
                            size="sm"
                            draggable="false"
                            class="hidden md:flex"
                        />
                        <UTooltip v-if="page.published" :text="t('cms.pages.viewOnSite')">
                            <UButton
                                :to="`/${page.slug}`"
                                target="_blank"
                                icon="i-lucide-external-link"
                                :aria-label="t('cms.pages.viewOnSite')"
                                color="neutral"
                                variant="ghost"
                                size="sm"
                                draggable="false"
                                class="hidden md:flex"
                            />
                        </UTooltip>
                        <div v-if="canReorder && group.pages.length > 1" class="flex flex-col">
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
                    </div>
                </div>
            </AdminCard>
        </template>

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
                <div class="flex w-full justify-end gap-2">
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
