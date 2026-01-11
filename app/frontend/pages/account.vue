<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import { CORE_ACCOUNT_TABS, type AccountTabItem } from '~/config/account-tabs';
import { PROJECT_ACCOUNT_TABS } from '~/config/account-tabs-ext';

definePageMeta({
    middleware: 'auth',
    auth: true,
});

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

// Merge, filter by condition, and sort tabs
const tabs = computed(() => {
    const allTabs: AccountTabItem[] = [...CORE_ACCOUNT_TABS, ...PROJECT_ACCOUNT_TABS];
    return allTabs
        .filter((tab) => !tab.condition || tab.condition())
        .sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
});

// Convert tabs to UTabs format
const tabItems = computed(() => {
    return tabs.value.map((tab) => ({
        value: tab.id,
        label: t(tab.label),
        icon: tab.icon,
    }));
});

// Active tab state - use query param or default to first tab
const activeTabId = computed({
    get: () => {
        const tabParam = route.query.tab as string;
        const validTab = tabs.value.find((t) => t.id === tabParam);
        return validTab ? tabParam : tabs.value[0]?.id || 'account';
    },
    set: (value: string) => {
        router.replace({ query: { ...route.query, tab: value } });
    },
});

// Get the active tab configuration
const activeTab = computed(() => {
    return tabs.value.find((t) => t.id === activeTabId.value) || tabs.value[0];
});

// Handle tab change from UTabs
function onTabChange(key: string | number) {
    activeTabId.value = String(key);
}
</script>

<template>
    <div class="page-box">
        <UiPageTitleBanner compact>
            {{ t('core.account.title') }}
            <template #subtitle>
                {{ t('core.account.subtitle') }}
            </template>
        </UiPageTitleBanner>

        <ClientOnly>
            <!-- Tab Navigation -->
            <UTabs :items="tabItems" :model-value="activeTabId" class="mb-6" @update:model-value="onTabChange" />

            <!-- Tab Content -->
            <component :is="activeTab?.component" v-if="activeTab" />

            <template #fallback>
                <div class="space-y-6">
                    <LoadingSkeleton class="h-48" />
                    <LoadingSkeleton class="h-48" />
                </div>
            </template>
        </ClientOnly>
    </div>
</template>
