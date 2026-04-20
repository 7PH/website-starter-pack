<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import { useMyPendingInvitations } from '~/composables/organizations/useOrganizationInvitations';

const { t } = useI18n();
const auth = useAuth();
const config = useRuntimeConfig();

const invitationsEnabled = computed(() => String(config.public.orgInvitationsEnabled) === 'true');

const { invitations, refresh, accept, decline } = useMyPendingInvitations();

onMounted(() => {
    if (invitationsEnabled.value) refresh();
});

async function onAccept(invitation: OrganizationInvitationRead) {
    const ok = await accept(invitation);
    if (ok) await auth.refreshToken();
}
</script>

<template>
    <div class="space-y-4">
        <p class="explainer">{{ t('core.organizations.whatIsAnOrg') }}</p>

        <div v-if="invitationsEnabled && invitations.length > 0" class="invitations">
            <h3 class="invitations-title">{{ t('core.organizations.pendingInvitations') }}</h3>
            <ul class="invitation-list">
                <li v-for="inv in invitations" :key="inv.id" class="invitation-item">
                    <div class="invitation-info">
                        <div class="invitation-org">
                            {{ t('core.organizations.invitationFrom', { orgName: inv.organization_name }) }}
                        </div>
                        <div class="invitation-meta">
                            <UBadge
                                v-if="inv.is_admin_invite"
                                :label="t('core.organizations.admin')"
                                color="info"
                                size="xs"
                            />
                            <UBadge v-else :label="t('core.organizations.member')" color="neutral" size="xs" />
                            <span v-if="inv.invited_by_name" class="invited-by">{{ inv.invited_by_name }}</span>
                        </div>
                    </div>
                    <div class="invitation-actions">
                        <UButton
                            :label="t('core.organizations.invitationAccept')"
                            icon="i-lucide-check"
                            size="xs"
                            color="primary"
                            @click="onAccept(inv)"
                        />
                        <UButton
                            :label="t('core.organizations.invitationDecline')"
                            icon="i-lucide-x"
                            size="xs"
                            color="neutral"
                            variant="outline"
                            @click="decline(inv)"
                        />
                    </div>
                </li>
            </ul>
        </div>

        <OrganizationsList />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.explainer {
    @apply text-sm text-gray-600 dark:text-gray-400;
}

.invitations {
    @apply rounded-lg border border-primary-200 dark:border-primary-900/40 p-4;
}

.invitations-title {
    @apply text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 m-0;
}

.invitation-list {
    @apply flex flex-col gap-3 list-none p-0 m-0;
}

.invitation-item {
    @apply flex items-center justify-between gap-4 p-3 rounded bg-white dark:bg-gray-800;
}

.invitation-info {
    @apply flex flex-col gap-1;
}

.invitation-org {
    @apply text-sm font-medium text-gray-900 dark:text-gray-100;
}

.invitation-meta {
    @apply flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400;
}

.invited-by {
    @apply text-xs text-gray-500;
}

.invitation-actions {
    @apply flex gap-2;
}
</style>
