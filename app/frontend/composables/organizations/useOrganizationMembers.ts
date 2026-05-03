// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { Ref } from 'vue';
import { createInvitation } from '~/utils/api/invitations';
import { previewLabel } from '~/utils/formatters';

export interface MemberManagementCallbacks {
    onSelfDemoted?: () => void;
    onAuthRefreshNeeded?: () => void;
    onInvitationSent?: () => void;
}

/**
 * Composable for managing organization members.
 * Handles invitations, removals, and role/premium changes.
 *
 * When `ORG_INVITATIONS_ENABLED` is true, `inviteMember` sends an email
 * invitation. Otherwise it directly adds the user.
 */
export function useOrganizationMembers(
    orgId: Ref<number>,
    refreshOrg: () => void,
    callbacks?: MemberManagementCallbacks,
) {
    const api = useApi();
    const modal = useModalStore();
    const config = useRuntimeConfig();
    const { t } = useI18n();
    const { showSuccess, showError } = useToastHelpers();

    const showAddMemberModal = ref(false);
    const isAddingMember = ref(false);

    const invitationsEnabled = computed(() => String(config.public.orgInvitationsEnabled) === 'true');

    /**
     * Either send an invitation email or directly add the user to the org.
     */
    async function inviteMember(email: string, isAdmin: boolean) {
        isAddingMember.value = true;
        try {
            if (invitationsEnabled.value) {
                await createInvitation(orgId.value, { email, is_admin: isAdmin });
                showSuccess(
                    t('core.organizations.invitationSent'),
                    t('core.organizations.invitationSentDescription', { email }),
                );
                callbacks?.onInvitationSent?.();
            } else {
                await api.post(`/organizations/${orgId.value}/members`, { email, is_admin: isAdmin });
                showSuccess(
                    t('core.organizations.addMemberSuccess'),
                    t('core.organizations.addMemberSuccessDescription', { email }),
                );
                refreshOrg();
            }
            showAddMemberModal.value = false;
        } catch (error: unknown) {
            showError(
                error,
                invitationsEnabled.value
                    ? 'core.organizations.invitationSendFailed'
                    : 'core.organizations.addMemberFailed',
            );
        } finally {
            isAddingMember.value = false;
        }
    }

    async function toggleMemberAdmin(member: OrganizationMemberRead, currentUserId?: number) {
        const isDemotingSelf = member.is_admin && currentUserId !== undefined && member.user_id === currentUserId;
        if (isDemotingSelf) {
            const confirmed = await modal.open('confirm', {
                title: t('core.organizations.demoteSelfTitle'),
                message: t('core.organizations.demoteSelfConfirm'),
                confirmText: t('core.common.confirm'),
                confirmColor: 'warning',
            });
            if (!confirmed) return;
        }

        try {
            await api.patch(`/organizations/${orgId.value}/members/${member.user_id}`, {
                is_admin: !member.is_admin,
            });
            showSuccess(t('core.organizations.memberUpdated'));

            if (isDemotingSelf && callbacks?.onSelfDemoted) {
                callbacks.onSelfDemoted();
                return;
            }

            refreshOrg();
            callbacks?.onAuthRefreshNeeded?.();
        } catch (error: unknown) {
            showError(error, 'core.organizations.memberUpdateFailed');
        }
    }

    async function toggleMemberPremium(member: OrganizationMemberRead) {
        try {
            await api.patch(`/organizations/${orgId.value}/members/${member.user_id}`, {
                is_premium: !member.has_premium_seat,
            });
            showSuccess(t('core.organizations.memberUpdated'));
            refreshOrg();
        } catch (error: unknown) {
            showError(error, 'core.organizations.memberUpdateFailed');
        }
    }

    async function removeMember(member: OrganizationMemberRead) {
        const memberName = previewLabel(member);
        const confirmed = await modal.open('confirm', {
            title: t('core.organizations.removeMemberTitle'),
            message: t('core.organizations.removeMemberConfirm', { name: memberName }),
            confirmText: t('core.common.delete'),
            confirmColor: 'error',
        });
        if (!confirmed) return;

        try {
            await api.delete(`/organizations/${orgId.value}/members/${member.user_id}`);
            showSuccess(
                t('core.organizations.removeMemberSuccess'),
                t('core.organizations.removeMemberSuccessDescription', { name: memberName }),
            );
            refreshOrg();
        } catch (error: unknown) {
            showError(error, 'core.organizations.removeMemberFailed');
        }
    }

    return {
        showAddMemberModal,
        isAddingMember,
        invitationsEnabled,
        inviteMember,
        toggleMemberAdmin,
        toggleMemberPremium,
        removeMember,
    };
}

export type QuotaState = 'none' | 'ok' | 'warn' | 'exceeded';

/**
 * Computed helpers for organization quota status.
 */
export function useOrganizationQuota(org: Ref<OrganizationRead | null | undefined>) {
    const isOverQuota = computed(() => {
        if (!org.value) return false;
        return org.value.stripe_premium && (org.value.premium_member_count ?? 0) > org.value.stripe_quota;
    });

    const canAddPremium = computed(() => {
        if (!org.value || !org.value.stripe_premium) return false;
        return (org.value.premium_member_count ?? 0) < org.value.stripe_quota;
    });

    const quotaState = computed<QuotaState>(() => {
        if (!org.value || !org.value.stripe_premium) return 'none';
        const used = org.value.premium_member_count ?? 0;
        const total = org.value.stripe_quota || 0;
        if (total <= 0) return 'none';
        if (used > total) return 'exceeded';
        const ratio = used / total;
        if (ratio >= 0.8) return 'warn';
        return 'ok';
    });

    return {
        isOverQuota,
        canAddPremium,
        quotaState,
    };
}
