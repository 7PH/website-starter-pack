// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { Ref } from 'vue';

export interface MemberManagementCallbacks {
    /** Called after successfully demoting self - use to redirect */
    onSelfDemoted?: () => void;
    /** Called after any member change to refresh auth state */
    onAuthRefreshNeeded?: () => void;
}

/**
 * Composable for managing organization members.
 * Handles adding, removing, and updating member roles and premium status.
 */
export function useOrganizationMembers(
    orgId: Ref<number>,
    refreshOrg: () => void,
    callbacks?: MemberManagementCallbacks,
) {
    const api = useApi();
    const modal = useModalStore();
    const { t } = useI18n();
    const { showSuccess, showError } = useToastHelpers();

    // Add member modal state
    const showAddMemberModal = ref(false);
    const addMemberEmail = ref('');
    const addMemberAsAdmin = ref(false);
    const isAddingMember = ref(false);

    /**
     * Add a new member to the organization.
     */
    async function addMember() {
        isAddingMember.value = true;
        try {
            await api.post(`/organizations/${orgId.value}/members`, {
                email: addMemberEmail.value,
                is_admin: addMemberAsAdmin.value,
            });
            showSuccess(
                t('core.organizations.addMemberSuccess'),
                t('core.organizations.addMemberSuccessDescription', { email: addMemberEmail.value }),
            );
            showAddMemberModal.value = false;
            addMemberEmail.value = '';
            addMemberAsAdmin.value = false;
            refreshOrg();
        } catch (error: unknown) {
            showError(error, 'core.organizations.addMemberFailed');
        } finally {
            isAddingMember.value = false;
        }
    }

    /**
     * Toggle a member's admin status.
     * @param member The member to update
     * @param currentUserId Optional current user ID to check for self-demotion
     */
    async function toggleMemberAdmin(member: OrganizationMemberRead, currentUserId?: number) {
        // Check for self-demotion
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

            // Handle self-demotion redirect
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

    /**
     * Toggle a member's premium seat status.
     */
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

    /**
     * Remove a member from the organization.
     */
    async function removeMember(member: OrganizationMemberRead) {
        const memberName = `${member.first_name} ${member.last_name}`.trim() || member.email;
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

    /**
     * Reset the add member form state.
     */
    function resetAddMemberForm() {
        addMemberEmail.value = '';
        addMemberAsAdmin.value = false;
    }

    return {
        // Add member modal state
        showAddMemberModal,
        addMemberEmail,
        addMemberAsAdmin,
        isAddingMember,
        // Functions
        addMember,
        toggleMemberAdmin,
        toggleMemberPremium,
        removeMember,
        resetAddMemberForm,
    };
}

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

    return {
        isOverQuota,
        canAddPremium,
    };
}
