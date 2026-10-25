<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Admin sidebar content (header, filter, grouped links), shared by the desktop sidebar and the mobile drawer.
const props = defineProps<{
    /** Desktop icon rail */
    collapsed?: boolean;
    /** Drawer variant: bigger touch targets, close button */
    mobile?: boolean;
}>();

const emit = defineEmits<{ expand: []; close: [] }>();

const route = useRoute();
const { groups, text } = useAdminNav();

const filter = ref('');
const input = useTemplateRef('input');

const shown = computed(() => (props.collapsed ? groups.value : filterAdminNav(groups.value, filter.value)));

function openFirstMatch(event: KeyboardEvent) {
    const first = shown.value.flatMap((g) => g.items).find((i) => !i.external && i.to);
    if (!first?.to) return;
    clearFilter(event);
    navigateTo(first.to);
}

function clearFilter(event: KeyboardEvent) {
    filter.value = '';
    (event.target as HTMLElement).blur();
}

defineExpose({ focus: () => input.value?.inputRef?.focus() });
</script>

<template>
    <div class="flex min-h-0 flex-1 flex-col">
        <div
            class="flex items-center gap-2"
            :class="
                mobile ? 'py-1.5 pr-1.5 pl-4.5' : collapsed ? 'justify-center px-4 pt-4.5 pb-3' : 'px-4 pt-4.5 pb-3'
            "
        >
            <UIcon name="i-lucide-shield" class="size-4.5 shrink-0 text-error" />
            <span v-if="!collapsed" class="flex-1 truncate text-base font-extrabold text-highlighted">
                {{ text('Admin', 'cms.nav.editSite') }}
            </span>
            <UButton
                v-if="mobile"
                icon="i-lucide-x"
                color="neutral"
                variant="ghost"
                size="xl"
                :aria-label="text('Close', 'cms.nav.close')"
                @click="emit('close')"
            />
        </div>

        <div v-if="collapsed" class="flex justify-center pb-2">
            <UTooltip :text="text('Filter pages', 'cms.nav.filter')" :content="{ side: 'right' }">
                <UButton
                    icon="i-lucide-search"
                    color="neutral"
                    variant="outline"
                    :aria-label="text('Filter pages', 'cms.nav.filter')"
                    class="h-8.5 w-10 justify-center"
                    @click="emit('expand')"
                />
            </UTooltip>
        </div>
        <div v-else class="px-3 pb-2.5" :class="{ 'pt-1': mobile }">
            <UInput
                ref="input"
                v-model="filter"
                icon="i-lucide-search"
                :size="mobile ? 'xl' : 'md'"
                :placeholder="text('Filter pages', 'cms.nav.filter')"
                class="w-full"
                @keydown.enter="openFirstMatch"
                @keydown.esc="clearFilter"
            >
                <template v-if="!mobile" #trailing>
                    <UKbd value="/" />
                </template>
            </UInput>
        </div>

        <nav
            class="flex min-h-0 flex-1 flex-col gap-3.5 overflow-y-auto px-2.5 pt-1 [scrollbar-width:thin]"
            :class="mobile ? 'pb-4' : 'pb-3'"
        >
            <div v-for="(group, index) in shown" :key="group.id" class="flex flex-col gap-0.5">
                <div v-if="collapsed && index > 0" class="mx-2 mb-2 border-t border-default" />
                <span
                    v-else-if="!collapsed"
                    class="pb-1 text-[11px] font-extrabold tracking-[.07em] text-dimmed uppercase"
                    :class="mobile ? 'px-3' : 'px-2.5'"
                >
                    {{ group.label }}
                </span>
                <UTooltip
                    v-for="item in group.items"
                    :key="item.to ?? item.href"
                    :text="item.badge ? `${item.label} · ${item.badge}` : item.label"
                    :disabled="!collapsed"
                    :content="{ side: 'right', sideOffset: 8 }"
                    :ui="{ content: 'bg-inverted text-inverted ring-0 h-auto px-2.5 py-1.5 text-[13px] font-bold' }"
                >
                    <NuxtLink
                        :to="item.href ?? item.to"
                        :target="item.external ? '_blank' : undefined"
                        :aria-label="collapsed ? item.label : undefined"
                        class="flex items-center rounded-lg transition-colors"
                        :class="[
                            mobile
                                ? 'min-h-11 gap-3 rounded-[10px] px-3 text-[15px]'
                                : collapsed
                                  ? 'justify-center py-2.25 text-sm'
                                  : 'gap-2.5 px-2.5 py-1.75 text-sm',
                            isAdminNavActive(route.path, item.to)
                                ? 'bg-primary-100 font-bold text-primary-700 dark:bg-primary-500/20 dark:text-primary-300'
                                : 'font-semibold text-muted hover:bg-elevated hover:text-highlighted',
                        ]"
                    >
                        <span class="relative flex">
                            <UIcon :name="item.icon" :class="mobile ? 'size-4.5' : 'size-4'" />
                            <span
                                v-if="collapsed && item.badge"
                                class="absolute -top-0.75 -right-1 size-2 rounded-full ring-2 ring-bg"
                                :class="item.badgeTone === 'error' ? 'bg-error' : 'bg-primary'"
                            />
                        </span>
                        <template v-if="!collapsed">
                            <span class="flex-1 truncate">{{ item.label }}</span>
                            <span
                                v-if="item.badge"
                                class="min-w-4.5 rounded-full px-1.5 py-px text-center text-[11px] font-extrabold text-white"
                                :class="item.badgeTone === 'error' ? 'bg-error' : 'bg-primary'"
                            >
                                {{ item.badge }}
                            </span>
                            <UIcon v-if="item.external" name="i-lucide-external-link" class="size-3 opacity-55" />
                        </template>
                    </NuxtLink>
                </UTooltip>
            </div>
            <span
                v-if="!shown.length"
                class="text-dimmed"
                :class="mobile ? 'px-3 py-2 text-sm' : 'px-2.5 py-2 text-[13px]'"
            >
                {{ text(`No page matches “${filter}”`, 'cms.nav.noMatch', { query: filter }) }}
            </span>
        </nav>
    </div>
</template>
