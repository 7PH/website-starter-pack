<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
const props = defineProps<{
    org: OrganizationRead;
    isAdminView: boolean;
    canAddPremium: boolean;
    showAddMemberModal: boolean;
    addMemberEmail: string;
    addMemberAsAdmin: boolean;
    isAddingMember: boolean;
}>();

const emit = defineEmits<{
    'update:showAddMemberModal': [value: boolean];
    'update:addMemberEmail': [value: string];
    'update:addMemberAsAdmin': [value: boolean];
    addMember: [];
    toggleAdmin: [member: OrganizationMemberRead];
    togglePremium: [member: OrganizationMemberRead];
    removeMember: [member: OrganizationMemberRead];
}>();

const { t } = useI18n();

const memberColumns = [
    { accessorKey: 'email', header: t('core.organizations.email') },
    { accessorKey: 'name', header: t('core.organizations.name') },
    { accessorKey: 'role', header: t('core.organizations.admin') },
    { accessorKey: 'premium', header: t('core.organizations.premium') },
    { accessorKey: 'actions', header: '' },
];

function getMember(row: { original: unknown }): OrganizationMemberRead {
    return row.original as OrganizationMemberRead;
}
</script>

<template>
    <UCard class="members-card">
        <template #header>
            <UiCardHeader :title="`${t('core.organizations.members')} (${org.member_count})`">
                <template #actions>
                    <UButton
                        v-if="!org.deleted_at"
                        :label="t('core.organizations.addMember')"
                        icon="i-lucide-plus"
                        size="sm"
                        @click="emit('update:showAddMemberModal', true)"
                    />
                </template>
            </UiCardHeader>
        </template>

        <UTable :columns="memberColumns" :data="org.members" class="members-table">
            <template #email-cell="{ row }">
                <NuxtLink v-if="isAdminView" :to="`/admin/users/${row.original.user_id}`" class="member-link">
                    {{ row.original.email }}
                </NuxtLink>
                <span v-else>{{ row.original.email }}</span>
            </template>

            <template #name-cell="{ row }"> {{ row.original.first_name }} {{ row.original.last_name }} </template>

            <template #role-cell="{ row }">
                <UBadge
                    :label="row.original.is_admin ? t('core.organizations.admin') : t('core.organizations.member')"
                    :color="row.original.is_admin ? 'info' : 'neutral'"
                />
            </template>

            <template #premium-cell="{ row }">
                <UBadge v-if="row.original.has_premium_seat" :label="t('core.organizations.premium')" color="warning" />
                <span v-else class="text-gray-500 dark:text-gray-400">-</span>
            </template>

            <template #actions-cell="{ row }">
                <div v-if="!org.deleted_at" class="actions">
                    <UTooltip
                        :text="
                            row.original.is_admin ? t('core.organizations.demoteTo') : t('core.organizations.promoteTo')
                        "
                    >
                        <UButton
                            :icon="row.original.is_admin ? 'i-lucide-shield-off' : 'i-lucide-shield'"
                            color="neutral"
                            variant="ghost"
                            size="xs"
                            @click="emit('toggleAdmin', getMember(row))"
                        />
                    </UTooltip>
                    <UTooltip
                        v-if="org.stripe_premium"
                        :text="
                            row.original.has_premium_seat
                                ? t('core.organizations.removePremium')
                                : canAddPremium
                                  ? t('core.organizations.grantPremium')
                                  : t('core.organizations.quotaExceeded')
                        "
                    >
                        <UButton
                            :icon="row.original.has_premium_seat ? 'i-lucide-star-off' : 'i-lucide-star'"
                            color="warning"
                            variant="ghost"
                            size="xs"
                            :disabled="!row.original.has_premium_seat && !canAddPremium"
                            @click="emit('togglePremium', getMember(row))"
                        />
                    </UTooltip>
                    <UTooltip :text="t('core.organizations.removeFromOrg')">
                        <UButton
                            icon="i-lucide-user-minus"
                            color="error"
                            variant="ghost"
                            size="xs"
                            @click="emit('removeMember', getMember(row))"
                        />
                    </UTooltip>
                </div>
            </template>
        </UTable>
    </UCard>

    <!-- Add Member Modal -->
    <UModal :open="showAddMemberModal" @update:open="emit('update:showAddMemberModal', $event)">
        <template #content>
            <UCard>
                <template #header>
                    <UiModalHeader
                        :title="t('core.organizations.addMember')"
                        @close="emit('update:showAddMemberModal', false)"
                    />
                </template>

                <form class="add-member-form" @submit.prevent="emit('addMember')">
                    <UFormField :label="t('core.organizations.email')" required>
                        <UInput
                            :model-value="addMemberEmail"
                            type="email"
                            :placeholder="t('core.organizations.emailPlaceholder')"
                            @update:model-value="emit('update:addMemberEmail', $event)"
                        />
                    </UFormField>
                    <UCheckbox
                        :model-value="addMemberAsAdmin"
                        :label="t('core.organizations.addAsAdmin')"
                        @update:model-value="emit('update:addMemberAsAdmin', Boolean($event))"
                    />
                    <UiFormActions>
                        <UButton
                            :label="t('core.organizations.cancel')"
                            color="neutral"
                            variant="outline"
                            @click="emit('update:showAddMemberModal', false)"
                        />
                        <UButton
                            type="submit"
                            :label="t('core.organizations.add')"
                            :loading="isAddingMember"
                            :disabled="!addMemberEmail"
                        />
                    </UiFormActions>
                </form>
            </UCard>
        </template>
    </UModal>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.member-link {
    @apply text-primary-500 no-underline;
}

.member-link:hover {
    @apply underline;
}

.actions {
    @apply flex gap-1;
}

.add-member-form {
    @apply flex flex-col gap-4;
}

.members-table {
    @apply max-h-[500px];
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
