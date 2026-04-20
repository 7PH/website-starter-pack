// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Organization invitations API service - mirrors backend/controllers/invitations.py
 * and the org-prefixed invitation endpoints in organizations.py.
 */

export function listOrgInvitations(orgId: number): Promise<OrganizationInvitationListResponse> {
    return useApi().get<OrganizationInvitationListResponse>(`/organizations/${orgId}/invitations`);
}

export function createInvitation(
    orgId: number,
    data: OrganizationInvitationCreate,
): Promise<OrganizationInvitationRead> {
    return useApi().post<OrganizationInvitationRead>(`/organizations/${orgId}/invitations`, data);
}

export function cancelInvitation(orgId: number, invitationId: number): Promise<void> {
    return useApi().delete(`/organizations/${orgId}/invitations/${invitationId}`);
}

export function listMyPendingInvitations(): Promise<OrganizationInvitationListResponse> {
    return useApi().get<OrganizationInvitationListResponse>('/invitations/pending');
}

export function previewInvitation(token: string): Promise<PendingInvitationPreview> {
    return useApi().get<PendingInvitationPreview>(`/invitations/${token}`);
}

export function acceptInvitation(token: string): Promise<void> {
    return useApi().post(`/invitations/${token}/accept`, {});
}

export function declineInvitation(token: string): Promise<void> {
    return useApi().post(`/invitations/${token}/decline`, {});
}
