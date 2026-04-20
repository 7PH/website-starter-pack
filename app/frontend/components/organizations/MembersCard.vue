<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { useOrganizationQuota } from '~/composables/organizations/useOrganizationMembers';
import { useOrganizationInvitations } from '~/composables/organizations/useOrganizationInvitations';
import { formatDate } from '~/utils/formatters';

const props = withDefaults(
    defineProps<{
        org: OrganizationRead;
        isAdminView: boolean;
        isOwner?: boolean;
        canAddPremium: boolean;
        showAddMemberModal: boolean;
        isAddingMember: boolean;
        currentUserId?: number;
    }>(),
    { isOwner: true, currentUserId: undefined },
);

const emit = defineEmits<{
    'update:showAddMemberModal': [value: boolean];
    invite: [email: string, isAdmin: boolean];
    toggleAdmin: [member: OrganizationMemberRead];
    togglePremium: [member: OrganizationMemberRead];
    removeMember: [member: OrganizationMemberRead];
}>();

const { t } = useI18n();
const config = useRuntimeConfig();
const modal = useModalStore();

const invitationsEnabled = computed(() => String(config.public.orgInvitationsEnabled) === 'true');

const orgRef = computed(() => props.org);
const orgId = computed(() => props.org.id);
const { quotaState } = useOrganizationQuota(orgRef);

const progressColor = computed(() => {
    switch (quotaState.value) {
        case 'exceeded':
            return 'error';
        case 'warn':
            return 'warning';
        default:
            return 'primary';
    }
});

const usedSeats = computed(() => props.org.premium_member_count ?? 0);
const totalSeats = computed(() => props.org.stripe_quota ?? 0);

const ownerCount = computed(() => (props.org.members ?? []).filter((m) => m.is_admin).length);

const isCurrentUserOnlyOwner = computed(() => {
    if (props.isAdminView || props.currentUserId === undefined) return false;
    if (ownerCount.value !== 1) return false;
    const onlyOwner = (props.org.members ?? []).find((m) => m.is_admin);
    return onlyOwner?.user_id === props.currentUserId;
});

const { invitations, refresh: refreshInvitations, cancel: cancelInvitation } = useOrganizationInvitations(orgId);

onMounted(() => {
    if (invitationsEnabled.value && props.isOwner) refreshInvitations();
});

watch(
    () => props.isAddingMember,
    (now, prev) => {
        if (invitationsEnabled.value && props.isOwner && prev && !now) refreshInvitations();
    },
);

const memberColumns = computed(() => {
    const cols = [
        { accessorKey: 'email', header: t('core.organizations.email') },
        { accessorKey: 'name', header: t('core.organizations.name') },
        { accessorKey: 'role', header: t('core.organizations.admin') },
        { accessorKey: 'premium', header: t('core.organizations.premium') },
    ];
    if (props.isOwner) cols.push({ accessorKey: 'actions', header: '' });
    return cols;
});

function getMember(row: { original: unknown }): OrganizationMemberRead {
    return row.original as OrganizationMemberRead;
}

function buildActions(member: OrganizationMemberRead) {
    const items = [];
    const isOnlyOwner = member.is_admin && ownerCount.value === 1;
    const premiumBlocked = !member.has_premium_seat && !props.canAddPremium;

    items.push({
        label: member.is_admin ? t('core.organizations.demoteTo') : t('core.organizations.promoteTo'),
        icon: member.is_admin ? 'i-lucide-shield-off' : 'i-lucide-shield',
        disabled: isOnlyOwner,
        onSelect: () => {
            if (isOnlyOwner) return;
            emit('toggleAdmin', member);
        },
    });

    if (props.org.stripe_premium) {
        items.push({
            label: member.has_premium_seat
                ? t('core.organizations.removePremium')
                : premiumBlocked
                  ? t('core.organizations.quotaExceeded')
                  : t('core.organizations.grantPremium'),
            icon: member.has_premium_seat ? 'i-lucide-star-off' : 'i-lucide-star',
            disabled: premiumBlocked,
            onSelect: () => {
                if (premiumBlocked) return;
                emit('togglePremium', member);
            },
        });
    }

    items.push({
        label: t('core.organizations.removeFromOrg'),
        icon: 'i-lucide-user-minus',
        color: 'error',
        disabled: isOnlyOwner,
        onSelect: () => {
            if (isOnlyOwner) return;
            emit('removeMember', member);
        },
    });

    return [items];
}

async function onCancelInvitation(invitation: OrganizationInvitationRead) {
    const confirmed = await modal.open('confirm', {
        title: t('core.organizations.invitationCancelTitle'),
        message: t('core.organizations.invitationCancelConfirm', { email: invitation.email }),
        confirmText: t('core.common.confirm'),
        confirmColor: 'error',
    });
    if (!confirmed) return;
    await cancelInvitation(invitation);
}

function handleInvite(email: string, isAdmin: boolean) {
    emit('invite', email, isAdmin);
}
</script>

<template>
    <UCard class="members-card">
        <template #header>
            <UiCardHeader :title="`${t('core.organizations.members')} (${org.member_count})`">
                <template #actions>
                    <UButton
                        v-if="isOwner && !org.deleted_at"
                        :label="t('core.organizations.addMember')"
                        icon="i-lucide-plus"
                        size="sm"
                        @click="emit('update:showAddMemberModal', true)"
                    />
                </template>
            </UiCardHeader>
        </template>

        <div class="members-body">
            <UAlert
                v-if="isCurrentUserOnlyOwner"
                color="warning"
                variant="subtle"
                icon="i-lucide-alert-triangle"
                :description="t('core.organizations.onlyOwnerAlert')"
            />

            <div v-if="org.stripe_premium">
                <div class="quota-header">
                    <span class="quota-label">
                        {{ t('core.organizations.seatsUsedDetailed', { used: usedSeats, total: totalSeats }) }}
                    </span>
                </div>
                <UProgress
                    :model-value="totalSeats > 0 ? Math.min(100, (usedSeats / totalSeats) * 100) : 0"
                    :color="progressColor"
                    class="mt-2"
                />
            </div>

            <UTable :columns="memberColumns" :data="org.members" class="members-table">
                <template #email-cell="{ row }">
                    <NuxtLink v-if="isAdminView" :to="`/admin/users/${row.original.user_id}`" class="member-link">
                        {{ row.original.email }}
                    </NuxtLink>
                    <span v-else>{{ row.original.email }}</span>
                </template>

                <template #name-cell="{ row }">{{ row.original.first_name }} {{ row.original.last_name }}</template>

                <template #role-cell="{ row }">
                    <UTooltip :text="t('core.organizations.roleTooltip')">
                        <UBadge
                            :label="
                                row.original.is_admin ? t('core.organizations.admin') : t('core.organizations.member')
                            "
                            :color="row.original.is_admin ? 'info' : 'neutral'"
                        />
                    </UTooltip>
                </template>

                <template #premium-cell="{ row }">
                    <UBadge
                        v-if="row.original.has_premium_seat"
                        :label="t('core.organizations.premium')"
                        color="warning"
                    />
                    <span v-else class="text-gray-500 dark:text-gray-400">-</span>
                </template>

                <template #actions-cell="{ row }">
                    <div v-if="isOwner && !org.deleted_at" class="actions">
                        <UDropdownMenu :items="buildActions(getMember(row))">
                            <UButton
                                icon="i-lucide-more-vertical"
                                color="neutral"
                                variant="ghost"
                                size="xs"
                                :aria-label="t('core.common.actions')"
                            />
                        </UDropdownMenu>
                    </div>
                </template>
            </UTable>

            <!-- Pending invitations (Owners only, when invitations flag is on) -->
            <div v-if="isOwner && invitationsEnabled && invitations.length > 0" class="pending-section">
                <h4 class="pending-title">{{ t('core.organizations.pendingInvitations') }}</h4>
                <ul class="pending-list">
                    <li v-for="inv in invitations" :key="inv.id" class="pending-item">
                        <div class="pending-info">
                            <div class="pending-email">{{ inv.email }}</div>
                            <div class="pending-meta">
                                <UBadge
                                    v-if="inv.is_admin_invite"
                                    :label="t('core.organizations.admin')"
                                    color="info"
                                    size="xs"
                                />
                                <UBadge v-else :label="t('core.organizations.member')" color="neutral" size="xs" />
                                <span class="pending-expiry">
                                    {{ t('core.organizations.invitationFrom', { orgName: '' }) }}
                                    · {{ formatDate(inv.expires_at) }}
                                </span>
                            </div>
                        </div>
                        <UButton
                            icon="i-lucide-x"
                            color="error"
                            variant="ghost"
                            size="xs"
                            :aria-label="t('core.organizations.invitationCancelTitle')"
                            @click="onCancelInvitation(inv)"
                        />
                    </li>
                </ul>
            </div>
        </div>
    </UCard>

    <OrganizationsInviteMemberModal
        :open="showAddMemberModal"
        :is-sending="isAddingMember"
        @update:open="emit('update:showAddMemberModal', $event)"
        @invite="handleInvite"
    />
</template>

<style scoped>
@reference "~/assets/css/main.css";

.members-body {
    @apply flex flex-col gap-4;
}

.member-link {
    @apply text-primary-500 no-underline;
}

.member-link:hover {
    @apply underline;
}

.actions {
    @apply flex justify-end;
}

.quota-header {
    @apply flex items-center justify-between;
}

.quota-label {
    @apply text-sm font-medium text-gray-700 dark:text-gray-300;
}

.pending-section {
    @apply border-t border-gray-200 dark:border-gray-700 pt-4;
}

.pending-title {
    @apply text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 m-0;
}

.pending-list {
    @apply flex flex-col gap-2 list-none p-0 m-0;
}

.pending-item {
    @apply flex items-center justify-between p-2 rounded bg-gray-50 dark:bg-gray-800;
}

.pending-info {
    @apply flex flex-col gap-1;
}

.pending-email {
    @apply text-sm text-gray-900 dark:text-gray-100;
}

.pending-meta {
    @apply flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400;
}

.pending-expiry {
    @apply text-xs text-gray-500;
}

.members-table :deep(table) {
    @apply w-full;
}

.members-table :deep(th:nth-child(1)),
.members-table :deep(td:nth-child(1)) {
    @apply w-[35%];
}

.members-table :deep(th:nth-child(2)),
.members-table :deep(td:nth-child(2)) {
    @apply w-[25%];
}

.members-table :deep(th:nth-child(3)),
.members-table :deep(td:nth-child(3)) {
    @apply w-[12%];
}

.members-table :deep(th:nth-child(4)),
.members-table :deep(td:nth-child(4)) {
    @apply w-[12%];
}

.members-table :deep(th:nth-child(5)),
.members-table :deep(td:nth-child(5)) {
    @apply w-[16%];
}
</style>
