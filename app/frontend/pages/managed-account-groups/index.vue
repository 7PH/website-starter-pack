<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['managed-accounts-enabled', 'auth'],
});

const { t } = useI18n();
const { showError, showSuccess } = useToastHelpers();
const composable = useManagedAccountGroup();
const modal = useModalStore();

const groups = ref<ManagedAccountGroupRead[]>([]);
const isLoading = ref(true);
const isCreating = ref(false);
const showCreateModal = ref(false);
const newGroupName = ref('');

async function refresh() {
    isLoading.value = true;
    try {
        groups.value = await composable.listGroups();
    } catch (error) {
        showError(error, 'core.managed_accounts.loadFailed');
    } finally {
        isLoading.value = false;
    }
}

onMounted(refresh);

async function handleCreate() {
    const name = newGroupName.value.trim();
    if (!name) return;
    isCreating.value = true;
    try {
        const created = await composable.createGroup({ name });
        groups.value = [created, ...groups.value];
        showSuccess(t('core.managed_accounts.createGroupSuccess'));
        newGroupName.value = '';
        showCreateModal.value = false;
    } catch (error) {
        showError(error, 'core.managed_accounts.createGroupFailed');
    } finally {
        isCreating.value = false;
    }
}

function shareUrl(token: string) {
    if (typeof window === 'undefined') return '';
    return `${window.location.origin}/c/${token}`;
}

async function doCopy(token: string) {
    try {
        await navigator.clipboard.writeText(shareUrl(token));
        showSuccess(t('core.managed_accounts.linkCopied'));
    } catch (error) {
        showError(error, 'core.managed_accounts.linkCopyFailed');
    }
}

async function copyShareLink(group: ManagedAccountGroupRead) {
    if (group.member_count === 0) {
        const confirmed = await modal.open('confirm', {
            icon: 'i-lucide-triangle-alert',
            tone: 'warning',
            confirmColor: 'warning',
            title: t('core.managed_accounts.emptyShareTitle'),
            message: t('core.managed_accounts.emptyShareMessage'),
            confirmText: t('core.managed_accounts.copyAnyway'),
            cancelText: t('core.common.cancel'),
        });
        if (!confirmed) return;
    }
    await doCopy(group.share_token);
}
</script>

<template>
    <div class="page-box">
        <UiPageTitleBanner compact>
            {{ t('core.managed_accounts.title') }}
            <template #subtitle>
                {{ t('core.managed_accounts.subtitle') }}
            </template>
            <template #actions>
                <UButton color="primary" icon="i-lucide-plus" @click="showCreateModal = true">
                    {{ t('core.managed_accounts.addGroup') }}
                </UButton>
            </template>
        </UiPageTitleBanner>

        <div class="groups-content">
            <div v-if="isLoading" class="py-8 text-center">
                <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin" />
            </div>

            <EmptyState
                v-else-if="!groups.length"
                :title="t('core.managed_accounts.emptyTitle')"
                :description="t('core.managed_accounts.emptyDescription')"
                icon="i-lucide-users"
            />

            <div v-else class="grid gap-3">
                <NuxtLink
                    v-for="group in groups"
                    :key="group.id"
                    :to="`/managed-account-groups/${group.id}`"
                    class="group-card"
                >
                    <div class="group-card__main">
                        <h3 class="group-card__title">{{ group.name }}</h3>
                        <p class="group-card__meta">
                            {{ t('core.managed_accounts.memberCount', { n: group.member_count }) }}
                        </p>
                    </div>
                    <UButton
                        color="neutral"
                        variant="ghost"
                        icon="i-lucide-link"
                        size="sm"
                        :title="t('core.managed_accounts.copyLink')"
                        @click.prevent.stop="copyShareLink(group)"
                    />
                </NuxtLink>
            </div>
        </div>

        <UModal v-model:open="showCreateModal">
            <template #content>
                <UCard>
                    <template #header>
                        <UiModalHeader
                            :title="t('core.managed_accounts.createGroupTitle')"
                            @close="showCreateModal = false"
                        />
                    </template>

                    <form class="create-form" @submit.prevent="handleCreate">
                        <UFormField :label="t('core.managed_accounts.groupName')" required>
                            <UInput
                                v-model="newGroupName"
                                :placeholder="t('core.managed_accounts.groupNamePlaceholder')"
                                autofocus
                                class="w-full"
                            />
                        </UFormField>
                        <!-- Hidden submit so Enter inside the field still triggers handleCreate. -->
                        <button type="submit" class="hidden" tabindex="-1" aria-hidden="true" />
                    </form>

                    <template #footer>
                        <UiFormActions>
                            <UButton
                                color="neutral"
                                variant="outline"
                                :label="t('core.common.cancel')"
                                @click="showCreateModal = false"
                            />
                            <UButton
                                :label="t('core.managed_accounts.createGroup')"
                                :loading="isCreating"
                                :disabled="!newGroupName.trim()"
                                @click="handleCreate"
                            />
                        </UiFormActions>
                    </template>
                </UCard>
            </template>
        </UModal>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.groups-content {
    @apply mx-auto;
}

.group-card {
    @apply flex items-center justify-between gap-3 px-4 py-3 rounded-lg
           border border-gray-200 dark:border-gray-700
           hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800
           transition-colors;
}

.group-card__main {
    @apply min-w-0 flex-1;
}

.group-card__title {
    @apply font-medium text-gray-900 dark:text-gray-100 truncate;
}

.group-card__meta {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.create-form {
    @apply flex flex-col gap-4;
}
</style>
