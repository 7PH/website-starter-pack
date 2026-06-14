<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['managed-accounts-enabled', 'auth'],
});

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuth();
const { showError, showSuccess } = useToastHelpers();
const composable = useManagedAccountGroup();
const modal = useModalStore();
const { shareUrl, copyShareLink: copyShare } = useShareLink();

const groupId = computed(() => Number(route.params.id));

const groups = ref<ManagedAccountGroupRead[]>([]);
const accounts = ref<ManagedAccountRead[]>([]);
const isLoading = ref(true);
const showAddAccount = ref(false);
const showBulkImport = ref(false);
const showEditGroup = ref(false);
const newAccountName = ref('');
const editGroupName = ref('');
const isMutating = ref(false);

const group = computed(() => groups.value.find((g) => g.id === groupId.value) || null);
const otherGroups = computed(() => groups.value.filter((g) => g.id !== groupId.value && !g.archived_at));

// UTable doesn't propagate the row generic into slot props, so cast once here.
const acc = (row: { original: unknown }) => row.original as ManagedAccountRead;

const accountColumns = [
    { accessorKey: 'display_name', header: () => t('core.managed_accounts.accountName') },
    { accessorKey: 'code', header: () => t('core.managed_accounts.code') },
    { accessorKey: 'actions', header: '' },
];

const groupMenu = computed(() => [
    [
        {
            label: t('core.managed_accounts.rename'),
            icon: 'i-lucide-pencil',
            onSelect: () => {
                showEditGroup.value = true;
            },
        },
        {
            label: t('core.managed_accounts.rotateToken'),
            icon: 'i-lucide-refresh-cw',
            onSelect: () => rotateLink(),
        },
    ],
    [
        {
            label: t('core.managed_accounts.deleteGroup'),
            icon: 'i-lucide-trash-2',
            color: 'error' as const,
            onSelect: () => deleteGroup(),
        },
    ],
]);

function rowMenu(account: ManagedAccountRead) {
    const moveItems = otherGroups.value.map((g) => ({
        label: t('core.managed_accounts.moveTo', { name: g.name }),
        icon: 'i-lucide-arrow-right-left',
        onSelect: () => moveAccount(account, g.id),
    }));
    return [
        ...(moveItems.length ? [moveItems] : []),
        [
            {
                label: t('core.managed_accounts.reissueCode'),
                icon: 'i-lucide-key-round',
                onSelect: () => reissueCode(account),
            },
            {
                label: t('core.managed_accounts.deleteAccount'),
                icon: 'i-lucide-trash-2',
                color: 'error' as const,
                onSelect: () => deleteAccount(account),
            },
        ],
    ];
}

async function loadAll() {
    isLoading.value = true;
    try {
        const [allGroups, accs] = await Promise.all([composable.listGroups(), composable.listAccounts(groupId.value)]);
        groups.value = allGroups;
        accounts.value = accs;
        if (group.value) editGroupName.value = group.value.name;
    } catch (error) {
        showError(error, 'core.managed_accounts.loadFailed');
    } finally {
        isLoading.value = false;
    }
}

onMounted(loadAll);

async function copyShareLink() {
    if (!group.value) return;
    if (accounts.value.length === 0) {
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
    await copyShare(group.value.share_token);
}

async function rotateLink() {
    if (!group.value) return;
    const confirmed = await modal.open('confirm', {
        icon: 'i-lucide-triangle-alert',
        tone: 'warning',
        confirmColor: 'warning',
        title: t('core.managed_accounts.rotateToken'),
        message: t('core.managed_accounts.confirmRotateToken'),
        confirmText: t('core.managed_accounts.rotateToken'),
        cancelText: t('core.common.cancel'),
    });
    if (!confirmed) return;
    isMutating.value = true;
    try {
        const updated = await composable.rotateShareToken(group.value.id);
        groups.value = groups.value.map((g) => (g.id === updated.id ? updated : g));
        showSuccess(t('core.managed_accounts.tokenRotated'));
    } catch (error) {
        showError(error, 'core.managed_accounts.tokenRotateFailed');
    } finally {
        isMutating.value = false;
    }
}

async function renameGroup() {
    if (!group.value) return;
    const name = editGroupName.value.trim();
    if (!name || name === group.value.name) {
        showEditGroup.value = false;
        return;
    }
    isMutating.value = true;
    try {
        const updated = await composable.updateGroup(group.value.id, { name });
        groups.value = groups.value.map((g) => (g.id === updated.id ? updated : g));
        showSuccess(t('core.managed_accounts.groupUpdated'));
        showEditGroup.value = false;
    } catch (error) {
        showError(error, 'core.managed_accounts.groupUpdateFailed');
    } finally {
        isMutating.value = false;
    }
}

async function deleteGroup() {
    if (!group.value) return;
    const confirmed = await modal.open('confirm', {
        icon: 'i-lucide-trash-2',
        tone: 'error',
        confirmColor: 'error',
        title: t('core.managed_accounts.deleteGroup'),
        message: t('core.managed_accounts.confirmDeleteGroup', { count: accounts.value.length }),
        confirmText: t('core.managed_accounts.deleteGroup'),
        cancelText: t('core.common.cancel'),
    });
    if (!confirmed) return;
    isMutating.value = true;
    try {
        await composable.deleteGroup(group.value.id);
        showSuccess(t('core.managed_accounts.groupDeleted'));
        await router.push('/managed-account-groups');
    } catch (error) {
        showError(error, 'core.managed_accounts.groupDeleteFailed');
    } finally {
        isMutating.value = false;
    }
}

async function addAccount() {
    const display_name = newAccountName.value.trim();
    if (!display_name) return;
    isMutating.value = true;
    try {
        const created = await composable.createAccount(groupId.value, { display_name });
        accounts.value = [...accounts.value, created.account];
        showSuccess(t('core.managed_accounts.accountCreated'));
        newAccountName.value = '';
        showAddAccount.value = false;
    } catch (error) {
        showError(error, 'core.managed_accounts.accountCreateFailed');
    } finally {
        isMutating.value = false;
    }
}

async function reissueCode(account: ManagedAccountRead) {
    const confirmed = await modal.open('confirm', {
        icon: 'i-lucide-key-round',
        tone: 'warning',
        confirmColor: 'warning',
        title: t('core.managed_accounts.reissueCode'),
        message: t('core.managed_accounts.confirmReissueCode', { name: account.display_name || '' }),
        confirmText: t('core.managed_accounts.reissueCode'),
        cancelText: t('core.common.cancel'),
    });
    if (!confirmed) return;
    try {
        const updated = await composable.reissueCode(account.id);
        accounts.value = accounts.value.map((a) => (a.id === updated.id ? updated : a));
        showSuccess(t('core.managed_accounts.codeReissued'));
    } catch (error) {
        showError(error, 'core.managed_accounts.codeReissueFailed');
    }
}

async function moveAccount(account: ManagedAccountRead, destinationId: number) {
    try {
        await composable.updateAccount(account.id, { managed_account_group_id: destinationId });
        accounts.value = accounts.value.filter((a) => a.id !== account.id);
        showSuccess(t('core.managed_accounts.accountMoved'));
    } catch (error) {
        showError(error, 'core.managed_accounts.accountMoveFailed');
    }
}

async function deleteAccount(account: ManagedAccountRead) {
    const confirmed = await modal.open('confirm', {
        icon: 'i-lucide-trash-2',
        tone: 'error',
        confirmColor: 'error',
        title: t('core.managed_accounts.deleteAccount'),
        message: t('core.managed_accounts.confirmDeleteAccount', { name: account.display_name || '' }),
        confirmText: t('core.managed_accounts.deleteAccount'),
        cancelText: t('core.common.cancel'),
    });
    if (!confirmed) return;
    try {
        await composable.deleteAccount(account.id);
        accounts.value = accounts.value.filter((a) => a.id !== account.id);
        showSuccess(t('core.managed_accounts.accountDeleted'));
    } catch (error) {
        showError(error, 'core.managed_accounts.accountDeleteFailed');
    }
}

async function openAs(account: ManagedAccountRead) {
    try {
        const token = await composable.openAsAccount(account.id);
        // startOpenAs stashes the owner's token so the impersonation banner
        // can restore it via "back to my account".
        auth.startOpenAs(token);
        await router.push('/');
    } catch (error) {
        showError(error, 'core.managed_accounts.openAsFailed');
    }
}

async function copyCode(account: ManagedAccountRead) {
    if (!account.code) return;
    try {
        await navigator.clipboard.writeText(account.code);
        showSuccess(t('core.managed_accounts.codeCopied'));
    } catch (error) {
        showError(error, 'core.managed_accounts.codeCopyFailed');
    }
}
</script>

<template>
    <div class="page-box">
        <UiPageTitleBanner v-if="group" compact>
            {{ group.name }}
            <template #subtitle>
                <div class="banner-meta">
                    <span class="banner-meta__count">
                        {{ t('core.managed_accounts.accountsCount', { n: accounts.length }) }}
                    </span>
                    <span class="banner-meta__sep">·</span>
                    <code class="banner-meta__url" :title="shareUrl(group.share_token)">
                        {{ shareUrl(group.share_token) }}
                    </code>
                </div>
            </template>
            <template #actions>
                <UButton
                    icon="i-lucide-clipboard"
                    :label="t('core.managed_accounts.copyLink')"
                    @click="copyShareLink"
                />
                <UDropdownMenu :items="groupMenu">
                    <UButton
                        color="neutral"
                        variant="ghost"
                        icon="i-lucide-more-vertical"
                        :aria-label="t('core.common.actions')"
                    />
                </UDropdownMenu>
            </template>
        </UiPageTitleBanner>

        <div class="detail-content">
            <NuxtLink to="/managed-account-groups" class="back-link">
                <UIcon name="i-lucide-arrow-left" class="size-4" />
                {{ t('core.managed_accounts.backToList') }}
            </NuxtLink>

            <div v-if="isLoading" class="py-8 text-center">
                <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin" />
            </div>

            <template v-else-if="group">
                <section class="accounts-section">
                    <div class="section-header">
                        <h2 class="section-title">
                            {{ t('core.managed_accounts.accountsCount', { n: accounts.length }) }}
                        </h2>
                        <div class="section-actions">
                            <UButton
                                color="neutral"
                                variant="outline"
                                icon="i-lucide-upload"
                                size="sm"
                                :label="t('core.managed_accounts.import.import')"
                                @click="showBulkImport = true"
                            />
                            <UButton
                                color="primary"
                                icon="i-lucide-plus"
                                size="sm"
                                :label="t('core.managed_accounts.addAccount')"
                                @click="showAddAccount = true"
                            />
                        </div>
                    </div>

                    <EmptyState
                        v-if="!accounts.length"
                        :title="t('core.managed_accounts.noAccountsTitle')"
                        :description="t('core.managed_accounts.noAccountsDescription')"
                        icon="i-lucide-user"
                    />

                    <UCard v-else :ui="{ body: 'p-0 sm:p-0' }">
                        <UTable :columns="accountColumns" :data="accounts">
                            <template #display_name-cell="{ row }">
                                <span class="account-name">
                                    {{
                                        acc(row).display_name || t('core.user.display.fallback_id', { id: acc(row).id })
                                    }}
                                </span>
                            </template>

                            <template #code-cell="{ row }">
                                <div v-if="acc(row).code" class="code-cell">
                                    <code class="code-cell__value">
                                        {{ acc(row).code }}
                                    </code>
                                    <UButton
                                        color="neutral"
                                        variant="ghost"
                                        icon="i-lucide-clipboard"
                                        size="xs"
                                        :title="t('core.managed_accounts.copyCode')"
                                        @click="copyCode(acc(row))"
                                    />
                                </div>
                                <span v-else class="code-cell__missing">—</span>
                            </template>

                            <template #actions-cell="{ row }">
                                <div class="row-actions">
                                    <UButton
                                        color="neutral"
                                        variant="ghost"
                                        icon="i-lucide-log-in"
                                        size="sm"
                                        @click="openAs(acc(row))"
                                    >
                                        {{ t('core.managed_accounts.openAs') }}
                                    </UButton>
                                    <UDropdownMenu :items="rowMenu(acc(row))">
                                        <UButton
                                            color="neutral"
                                            variant="ghost"
                                            icon="i-lucide-more-vertical"
                                            size="sm"
                                            :aria-label="t('core.common.actions')"
                                        />
                                    </UDropdownMenu>
                                </div>
                            </template>
                        </UTable>
                    </UCard>
                </section>
            </template>
        </div>

        <ManagedAccountsBulkImportModal v-model:open="showBulkImport" :group-id="groupId" @imported="loadAll" />

        <UModal v-model:open="showAddAccount">
            <template #content>
                <UCard>
                    <template #header>
                        <UiModalHeader
                            :title="t('core.managed_accounts.addAccountTitle')"
                            @close="showAddAccount = false"
                        />
                    </template>

                    <form class="create-form" @submit.prevent="addAccount">
                        <UFormField :label="t('core.managed_accounts.accountName')" required>
                            <UInput
                                v-model="newAccountName"
                                :placeholder="t('core.managed_accounts.accountNamePlaceholder')"
                                autofocus
                                class="w-full"
                            />
                        </UFormField>
                        <button type="submit" class="hidden" tabindex="-1" aria-hidden="true" />
                    </form>

                    <template #footer>
                        <UiFormActions>
                            <UButton
                                color="neutral"
                                variant="outline"
                                :label="t('core.common.cancel')"
                                @click="showAddAccount = false"
                            />
                            <UButton
                                :label="t('core.managed_accounts.addAccount')"
                                :loading="isMutating"
                                :disabled="!newAccountName.trim()"
                                @click="addAccount"
                            />
                        </UiFormActions>
                    </template>
                </UCard>
            </template>
        </UModal>

        <UModal v-model:open="showEditGroup">
            <template #content>
                <UCard>
                    <template #header>
                        <UiModalHeader :title="t('core.managed_accounts.renameGroup')" @close="showEditGroup = false" />
                    </template>

                    <form class="create-form" @submit.prevent="renameGroup">
                        <UFormField :label="t('core.managed_accounts.groupName')" required>
                            <UInput v-model="editGroupName" autofocus class="w-full" />
                        </UFormField>
                        <button type="submit" class="hidden" tabindex="-1" aria-hidden="true" />
                    </form>

                    <template #footer>
                        <UiFormActions>
                            <UButton
                                color="neutral"
                                variant="outline"
                                :label="t('core.common.cancel')"
                                @click="showEditGroup = false"
                            />
                            <UButton
                                :label="t('core.managed_accounts.save')"
                                :loading="isMutating"
                                :disabled="!editGroupName.trim()"
                                @click="renameGroup"
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

.detail-content {
    @apply mx-auto pb-6 space-y-6;
}

.back-link {
    @apply inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700
           dark:text-gray-400 dark:hover:text-gray-200;
}

.banner-meta {
    @apply flex items-center gap-2 flex-wrap text-sm;
}

.banner-meta__count {
    @apply text-slate-700 dark:text-slate-300 font-medium;
}

.banner-meta__sep {
    @apply text-slate-400 dark:text-slate-500;
}

.banner-meta__url {
    @apply font-mono truncate text-slate-600 dark:text-slate-400
           max-w-xs sm:max-w-md md:max-w-lg;
}

.section-header {
    @apply flex items-center justify-between mb-3;
}

.section-title {
    @apply text-lg font-medium text-gray-900 dark:text-gray-100;
}

.section-actions {
    @apply flex items-center gap-2;
}

.account-name {
    @apply font-medium text-gray-900 dark:text-gray-100;
}

.code-cell {
    @apply flex items-center gap-2;
}

.code-cell__value {
    @apply font-mono text-sm tracking-wider text-gray-700 dark:text-gray-200
           bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded;
}

.code-cell__missing {
    @apply text-gray-400 dark:text-gray-500;
}

.row-actions {
    @apply flex items-center justify-end gap-1;
}

.create-form {
    @apply flex flex-col gap-4;
}
</style>
