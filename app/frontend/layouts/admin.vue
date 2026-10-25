<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
// Applied to every /admin/** page by middleware/admin.ts: global top bar, then the admin sidebar (a drawer below md).
import ImpersonationBanner from '~/components/admin/ImpersonationBanner.vue';
import ModalAuth from '~/components/modal/ModalAuth.vue';
import ModalConfirm from '~/components/modal/ModalConfirm.vue';
import PageHeaderDefault from '~/components/PageHeader.vue';

const PageHeader = useOverridable('PageHeader', PageHeaderDefault);
const { uiLocale } = useAppLocale();
const route = useRoute();
const auth = useAuth();
const { groups, text } = useAdminNav();

const COLLAPSED_KEY = 'starterpack-admin-sidebar-collapsed';
const collapsed = ref(readCollapsed());
const drawerOpen = ref(false);
const sidebarNav = useTemplateRef('sidebarNav');

function readCollapsed(): boolean {
    try {
        return localStorage.getItem(COLLAPSED_KEY) === '1';
    } catch {
        return false;
    }
}

watch(collapsed, (value) => {
    try {
        localStorage.setItem(COLLAPSED_KEY, value ? '1' : '0');
    } catch {
        // Storage blocked (private mode): the choice lasts until reload.
    }
});

const current = computed(() => {
    for (const group of groups.value) {
        const item = group.items.find((i) => isAdminNavActive(route.path, i.to));
        if (item) return { group: group.label, label: item.label };
    }
    return null;
});
const hasBadge = computed(() => groups.value.some((g) => g.items.some((i) => i.badge)));

function focusFilter() {
    collapsed.value = false;
    nextTick(() => sidebarNav.value?.focus());
}

// Ignored while typing in a field or the rich text editor, where Ctrl+B means bold.
defineShortcuts({
    '/': focusFilter,
    meta_b: () => (collapsed.value = !collapsed.value),
});

watch(
    () => route.fullPath,
    () => (drawerOpen.value = false),
);

onMounted(() => {
    if (auth.user?.is_admin) loadAdminNavBadges();
});
</script>

<template>
    <!-- UApp renders no element: the wrapper div is the flex column -->
    <div class="flex min-h-0 flex-1 flex-col bg-slate-50 dark:bg-slate-950">
        <UApp :locale="uiLocale">
            <ImpersonationBanner />
            <component :is="PageHeader" />

            <div class="flex h-14 shrink-0 items-center gap-1 border-b border-default bg-default px-2.5 md:hidden">
                <UButton
                    icon="i-lucide-menu"
                    color="neutral"
                    variant="ghost"
                    size="xl"
                    :aria-label="text('Menu', 'cms.nav.menu')"
                    class="relative"
                    @click="drawerOpen = true"
                >
                    <template #trailing>
                        <span
                            v-if="hasBadge"
                            class="absolute top-2 right-2 size-2 rounded-full bg-error ring-2 ring-bg"
                        />
                    </template>
                </UButton>
                <div class="flex min-w-0 flex-1 flex-col">
                    <span class="text-[11px] font-bold text-dimmed">
                        {{ text('Admin', 'cms.nav.editSite')
                        }}<template v-if="current"> · {{ current.group }}</template>
                    </span>
                    <span v-if="current" class="truncate text-[15px] font-extrabold text-highlighted">{{
                        current.label
                    }}</span>
                </div>
            </div>

            <div class="flex min-h-0 flex-1">
                <aside
                    class="hidden shrink-0 flex-col border-r border-default bg-default transition-[width] duration-200 ease-out md:flex"
                    :class="collapsed ? 'w-16' : 'w-63'"
                >
                    <AdminNav ref="sidebarNav" :collapsed="collapsed" @expand="focusFilter" />
                    <div class="border-t border-default p-2.5">
                        <UTooltip
                            :text="text('Expand', 'cms.nav.expand')"
                            :disabled="!collapsed"
                            :content="{ side: 'right' }"
                        >
                            <button
                                type="button"
                                class="flex w-full items-center gap-2.5 rounded-lg text-[13px] font-semibold text-muted transition-colors hover:bg-elevated"
                                :class="collapsed ? 'justify-center py-2.25' : 'px-2.5 py-1.75'"
                                :aria-label="collapsed ? text('Expand', 'cms.nav.expand') : undefined"
                                @click="collapsed = !collapsed"
                            >
                                <UIcon
                                    :name="collapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
                                    class="size-4"
                                />
                                <template v-if="!collapsed">
                                    <span class="flex-1 text-left">{{ text('Collapse', 'cms.nav.collapse') }}</span>
                                    <span class="flex gap-0.5"><UKbd value="meta" /><UKbd value="B" /></span>
                                </template>
                            </button>
                        </UTooltip>
                    </div>
                </aside>

                <main
                    class="flex min-h-0 min-w-0 flex-1 flex-col overflow-x-hidden overflow-y-auto p-4 md:px-8 md:py-7"
                >
                    <NuxtPage />
                </main>
            </div>

            <USlideover
                v-model:open="drawerOpen"
                side="left"
                :title="text('Admin', 'cms.nav.editSite')"
                :ui="{ overlay: 'bg-slate-950/50', content: 'w-[304px] max-w-[85vw] divide-y-0' }"
            >
                <template #content>
                    <AdminNav mobile @close="drawerOpen = false" />
                </template>
            </USlideover>

            <!-- Global modals -->
            <ModalConfirm />
            <ModalAuth />
        </UApp>
    </div>
</template>
