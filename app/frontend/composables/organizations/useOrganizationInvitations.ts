// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { Ref } from 'vue';
import {
    acceptInvitation,
    cancelInvitation,
    createInvitation,
    declineInvitation,
    listMyPendingInvitations,
    listOrgInvitations,
} from '~/utils/api/invitations';

/**
 * Manage pending invitations of a single organization (Owner side).
 */
export function useOrganizationInvitations(orgId: Ref<number>) {
    const { t } = useI18n();
    const { showSuccess, showError } = useToastHelpers();

    const invitations = ref<OrganizationInvitationRead[]>([]);
    const pending = ref(false);
    const isSending = ref(false);

    async function refresh() {
        pending.value = true;
        try {
            const res = await listOrgInvitations(orgId.value);
            invitations.value = res.items;
        } catch (error) {
            showError(error, 'core.errors.generic');
        } finally {
            pending.value = false;
        }
    }

    async function invite(email: string, isAdmin: boolean) {
        isSending.value = true;
        try {
            await createInvitation(orgId.value, { email, is_admin: isAdmin });
            showSuccess(
                t('core.organizations.invitationSent'),
                t('core.organizations.invitationSentDescription', { email }),
            );
            await refresh();
            return true;
        } catch (error) {
            showError(error, 'core.organizations.invitationSendFailed');
            return false;
        } finally {
            isSending.value = false;
        }
    }

    async function cancel(invitation: OrganizationInvitationRead) {
        try {
            await cancelInvitation(orgId.value, invitation.id);
            showSuccess(t('core.organizations.invitationCanceled'));
            await refresh();
        } catch (error) {
            showError(error, 'core.organizations.invitationCancelFailed');
        }
    }

    return { invitations, pending, isSending, refresh, invite, cancel };
}

/**
 * List the current user's pending invitations and accept/decline them inline.
 */
export function useMyPendingInvitations() {
    const { t } = useI18n();
    const { showSuccess, showError } = useToastHelpers();
    const invitations = ref<OrganizationInvitationRead[]>([]);
    const pending = ref(false);

    async function refresh() {
        pending.value = true;
        try {
            const res = await listMyPendingInvitations();
            invitations.value = res.items;
        } catch (error) {
            showError(error, 'core.errors.generic');
        } finally {
            pending.value = false;
        }
    }

    async function accept(invitation: OrganizationInvitationRead) {
        if (!invitation.token) return;
        try {
            await acceptInvitation(invitation.token);
            showSuccess(t('core.organizations.invitationAccepted'));
            await refresh();
            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
    }

    async function decline(invitation: OrganizationInvitationRead) {
        if (!invitation.token) return;
        try {
            await declineInvitation(invitation.token);
            showSuccess(t('core.organizations.invitationDeclined'));
            await refresh();
        } catch (error) {
            showError(error, 'core.errors.generic');
        }
    }

    return { invitations, pending, refresh, accept, decline };
}
