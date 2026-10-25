<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Editor for one page, free or fixed. `endpoint` is the admin URL of the page, used for both reading and saving.
import { autoSlug, cmsDraftKey, cmsLabel, hasReservedPrefix, isEmptyField, isShadowedSlug, slugify } from '~/utils/cms';
import { getErrorStatus } from '~/utils/errors';

const props = defineProps<{ endpoint: string }>();

// Google shows about this much; the backend accepts more.
const SEO_TITLE_MAX = 70;
const SEO_DESCRIPTION_MAX = 160;

interface PageForm {
    title: string;
    slug: string;
    published: boolean;
    seo_title: string;
    seo_description: string;
    cover: CmsMediaRead | null;
    fields: Record<string, unknown>;
}

const { t, locale } = useI18n();
const api = useApi();
const router = useRouter();
const modal = useModalStore();
const { showSuccess, showWarning } = useToastHelpers();
const showCmsError = useCmsErrorToast();

const [{ data: page, pending, error, refresh }, { data: templates }] = await Promise.all([
    // A 404 resolves to null, so "this page doesn't exist anymore" is told apart from other failures.
    useAsyncData<CmsPageAdminRead | null>(
        `cms-admin-${props.endpoint}`,
        () =>
            api.get<CmsPageAdminRead>(props.endpoint).catch((e) => {
                if (getErrorStatus(e) === 404) return null;
                throw e;
            }),
        { server: false },
    ),
    useAsyncData<CmsTemplateRead[]>('cms-templates', () => api.get('/cms/templates'), { server: false }),
]);

const template = computed(() => templates.value?.find((tpl) => tpl.name === page.value?.template));
const isFixed = computed(() => page.value?.fixed_key != null);
const heading = computed(() =>
    isFixed.value ? cmsLabel(template.value?.label, locale.value) : form.value.title || t('cms.pages.untitled'),
);

const form = ref<PageForm>(emptyForm());
const baseline = ref('');
const saving = ref(false);

function emptyForm(): PageForm {
    return {
        title: '',
        slug: '',
        published: false,
        seo_title: '',
        seo_description: '',
        cover: null,
        fields: {},
    };
}

watch(
    page,
    (p) => {
        if (!p) return;
        form.value = {
            title: p.title,
            slug: p.slug ?? '',
            published: p.published,
            seo_title: p.seo_title,
            seo_description: p.seo_description,
            cover: p.cover,
            fields: { ...p.fields },
        };
        baseline.value = JSON.stringify(form.value);
    },
    { immediate: true },
);

const isDirty = computed(() => !!page.value && JSON.stringify(form.value) !== baseline.value);
useUnsavedChangesWarning(isDirty);

// The address follows the title while it still matches it, until the page goes online once.
watch(
    () => form.value.title,
    (title, previous) => {
        const following = !form.value.slug || form.value.slug === titleSlug(previous);
        if (!page.value?.published_at && following) form.value.slug = titleSlug(title);
    },
);

const origin = useRequestURL().origin;
const pageUrl = computed(() => `${origin}/${slugify(form.value.slug)}`);
// A site route with the same address would always win over this page.
const routePaths = router.getRoutes().map((route) => route.path);
const isBlocked = (slug: string) => hasReservedPrefix(slug) || isShadowedSlug(slug, routePaths);
// Moved off blocked addresses like the backend does ("Login" -> "page-login"). Kept as is when that's blocked too: the warning tells why.
function titleSlug(title: string): string {
    const slug = autoSlug(title);
    return isBlocked(slug) && !isBlocked(`page-${slug}`) ? `page-${slug}` : slug;
}
const slugReserved = computed(() => hasReservedPrefix(slugify(form.value.slug)));
const slugShadowed = computed(() => isShadowedSlug(slugify(form.value.slug), routePaths));

const previewUrl = computed(() => (page.value && !isFixed.value ? `/admin/cms/preview/${page.value.id}` : null));
// The saved address, so "Open" never leads to an address that isn't online yet.
const publicUrl = computed(() => (page.value?.published && !isFixed.value ? `${origin}/${page.value.slug}` : null));

// Shares unsaved changes with an open preview tab, which refreshes on each change.
const draftKey = computed(() => (page.value?.id && !isFixed.value ? cmsDraftKey(page.value.id) : null));
function syncDraft() {
    if (!draftKey.value) return;
    try {
        if (isDirty.value) localStorage.setItem(draftKey.value, JSON.stringify({ ...payload(), slug: undefined }));
        else localStorage.removeItem(draftKey.value);
    } catch {
        // Storage unavailable: the preview falls back to the saved version.
    }
}
watch(form, syncDraft, { deep: true });
watch(isDirty, syncDraft);
// Leaving without saving (tab closed included) must not leave a stale draft for the next preview.
function clearDraft() {
    try {
        if (draftKey.value) localStorage.removeItem(draftKey.value);
    } catch {
        // Nothing to clean up.
    }
}
useEventListener('pagehide', clearDraft);
onBeforeUnmount(clearDraft);

function payload(): CmsPageUpdate {
    const f = form.value;
    const fields = Object.fromEntries(
        (template.value?.fields ?? []).map((field) => {
            const value = f.fields[field.name];
            if (field.type !== 'image') return [field.name, value];
            return [field.name, value ? { media_id: (value as CmsMediaRead).id } : null];
        }),
    );
    const common = { fields, seo_title: f.seo_title, seo_description: f.seo_description };
    if (isFixed.value) return common;
    return {
        ...common,
        title: f.title,
        slug: slugify(f.slug),
        published: f.published,
        cover_media_id: f.cover?.id ?? null,
    };
}

async function save() {
    const missing = template.value?.fields.find(
        (field) => field.required && isEmptyField(field, form.value.fields[field.name]),
    );
    if (missing) return showWarning(t('cms.pages.required', { field: cmsLabel(missing.label, locale.value) }));
    if (!isFixed.value && !form.value.title.trim()) return showWarning(t('cms.pages.titleRequired'));
    if (!isFixed.value && !slugify(form.value.slug)) return showWarning(t('cms.pages.slugRequired'));
    if (!isFixed.value && (slugReserved.value || slugShadowed.value)) return showWarning(t('cms.pages.slugReserved'));

    saving.value = true;
    try {
        // updated_at as loaded: the server refuses the save if the page changed since (another tab, a quick edit).
        page.value = await api.patch<CmsPageAdminRead>(props.endpoint, {
            ...payload(),
            updated_at: page.value?.updated_at,
        });
        showSuccess(t('cms.pages.saved'));
    } catch (e) {
        showCmsError(e, { fields: template.value?.fields, onReload: refresh });
    } finally {
        saving.value = false;
    }
}

async function remove() {
    const confirmed = await modal.open('confirm', {
        title: t('cms.pages.delete.title'),
        message: t('cms.pages.delete.message', { title: page.value?.title }),
        confirmText: t('cms.pages.delete.confirm'),
        confirmColor: 'error',
    });
    if (!confirmed) return;
    try {
        await api.delete(props.endpoint);
        baseline.value = JSON.stringify(form.value);
        showSuccess(t('cms.pages.delete.done'));
        await router.push('/admin/cms/pages');
    } catch (e) {
        showCmsError(e);
    }
}
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <NuxtLink
            to="/admin/cms/pages"
            class="inline-flex items-center gap-1 self-start text-sm font-semibold text-muted hover:text-highlighted"
        >
            <UIcon name="i-lucide-arrow-left" />
            {{ t('cms.pages.backToList') }}
        </NuxtLink>

        <div v-if="pending" class="flex justify-center py-16">
            <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary" />
        </div>

        <UAlert
            v-else-if="error || !page"
            color="error"
            variant="subtle"
            icon="i-lucide-file-x"
            :title="error ? t('cms.pages.loadError') : t('cms.pages.notFound')"
        />

        <form v-else class="flex flex-col gap-6" @submit.prevent="save">
            <AdminPageHeader :title="heading" :description="isFixed ? undefined : `/${page.slug}`">
                <template v-if="!isFixed" #badges>
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
                </template>
                <template v-if="publicUrl || previewUrl" #actions>
                    <UButton
                        v-if="publicUrl"
                        :to="publicUrl"
                        target="_blank"
                        :label="t('cms.pages.open')"
                        icon="i-lucide-external-link"
                        color="neutral"
                        variant="outline"
                        size="lg"
                    />
                    <UButton
                        v-if="previewUrl"
                        :to="previewUrl"
                        target="_blank"
                        :label="t('cms.pages.preview')"
                        icon="i-lucide-eye"
                        color="neutral"
                        variant="outline"
                        size="lg"
                    />
                </template>
            </AdminPageHeader>

            <div class="grid gap-6 lg:grid-cols-3">
                <div class="flex flex-col gap-6 lg:col-span-2">
                    <UCard v-if="!isFixed">
                        <div class="flex flex-col gap-4">
                            <UFormField :label="t('cms.pages.title')" :hint="`${form.title.length} / 200`" required>
                                <UInput v-model="form.title" :maxlength="200" size="lg" class="w-full" />
                            </UFormField>
                            <UFormField :label="t('cms.pages.slug')" :description="t('cms.pages.slugHelp')">
                                <UInput
                                    v-model="form.slug"
                                    :maxlength="200"
                                    class="w-full"
                                    @blur="form.slug = slugify(form.slug)"
                                />
                                <template #help>
                                    <span class="break-all">{{ pageUrl }}</span>
                                </template>
                            </UFormField>
                            <UAlert
                                v-if="slugReserved || slugShadowed"
                                color="warning"
                                variant="subtle"
                                icon="i-lucide-triangle-alert"
                                :title="slugReserved ? t('cms.pages.slugReserved') : t('cms.pages.slugShadowed')"
                            />
                        </div>
                    </UCard>

                    <UCard v-if="template?.fields.length">
                        <div class="flex flex-col gap-6">
                            <CmsField
                                v-for="field in template.fields"
                                :key="field.name"
                                v-model="form.fields[field.name]"
                                :field="field"
                            />
                        </div>
                    </UCard>

                    <UCard>
                        <UCollapsible>
                            <UButton
                                :label="t('cms.pages.seo.title')"
                                icon="i-lucide-search"
                                trailing-icon="i-lucide-chevron-down"
                                color="neutral"
                                variant="ghost"
                                block
                                class="justify-between"
                            />
                            <template #content>
                                <div class="flex flex-col gap-4 pt-4">
                                    <p class="text-sm text-muted">
                                        {{ t('cms.pages.seo.help') }}
                                    </p>
                                    <UFormField
                                        :label="t('cms.pages.seo.seoTitle')"
                                        :hint="`${(form.seo_title || form.title).length} / ${SEO_TITLE_MAX}`"
                                        :help="
                                            !form.seo_title && form.title.length > SEO_TITLE_MAX
                                                ? t('cms.pages.seo.titleTooLong')
                                                : undefined
                                        "
                                    >
                                        <UInput
                                            v-model="form.seo_title"
                                            :maxlength="SEO_TITLE_MAX"
                                            :placeholder="form.title"
                                            class="w-full"
                                        />
                                    </UFormField>
                                    <UFormField
                                        :label="t('cms.pages.seo.seoDescription')"
                                        :hint="`${form.seo_description.length} / ${SEO_DESCRIPTION_MAX}`"
                                    >
                                        <UTextarea
                                            v-model="form.seo_description"
                                            :maxlength="SEO_DESCRIPTION_MAX"
                                            :placeholder="page.seo_description_auto"
                                            :rows="3"
                                            autoresize
                                            class="w-full"
                                        />
                                    </UFormField>
                                </div>
                            </template>
                        </UCollapsible>
                    </UCard>
                </div>

                <div v-if="!isFixed" class="flex flex-col gap-6">
                    <UCard>
                        <USwitch
                            v-model="form.published"
                            :label="t('cms.pages.published')"
                            :description="form.published ? t('cms.pages.publishedOn') : t('cms.pages.publishedOff')"
                        />
                    </UCard>
                    <UCard>
                        <UFormField :label="t('cms.pages.cover')" :description="t('cms.pages.coverHelp')">
                            <CmsImageInput v-model="form.cover" />
                        </UFormField>
                    </UCard>
                    <UButton
                        :label="t('cms.pages.delete.button')"
                        icon="i-lucide-trash-2"
                        color="error"
                        variant="ghost"
                        class="self-start"
                        @click="remove"
                    />
                </div>
            </div>

            <!-- Stays in reach on long pages. -->
            <div
                class="sticky bottom-0 z-20 -mx-4 flex items-center justify-end gap-4 border-t border-default bg-default/90 px-4 py-3 backdrop-blur md:-mx-8 md:px-8"
            >
                <span class="text-sm" :class="isDirty ? 'text-amber-600 dark:text-amber-400' : 'text-muted'">
                    {{ isDirty ? t('cms.pages.unsaved') : t('cms.pages.allSaved') }}
                </span>
                <UButton
                    type="submit"
                    :label="t('cms.pages.save')"
                    icon="i-lucide-check"
                    :loading="saving"
                    :disabled="!isDirty"
                />
            </div>
        </form>
    </div>
</template>
