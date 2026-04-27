// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * CRUD for managed account groups and the managed accounts inside them.
 *
 * The owner (a regular signed-in user) lists / creates / archives groups,
 * and adds / renames / moves / removes managed accounts within them.
 *
 * Managed accounts themselves never use this composable — they sign in via
 * `useAccessCode().signInWithCode(...)` after the public picker.
 */
export function useManagedAccountGroup() {
    const api = useApi();

    // ─── group ops ───

    function listGroups() {
        return api.get<ManagedAccountGroupRead[]>('/me/managed-account-groups');
    }

    function createGroup(body: ManagedAccountGroupCreate) {
        return api.post<ManagedAccountGroupRead>('/me/managed-account-groups', body);
    }

    function updateGroup(groupId: number, body: ManagedAccountGroupUpdate) {
        return api.patch<ManagedAccountGroupRead>(`/me/managed-account-groups/${groupId}`, body);
    }

    function deleteGroup(groupId: number) {
        return api.delete<void>(`/me/managed-account-groups/${groupId}`);
    }

    function rotateShareToken(groupId: number) {
        return api.post<ManagedAccountGroupRead>(`/me/managed-account-groups/${groupId}/rotate-token`);
    }

    // ─── managed account ops ───

    function listAccounts(groupId: number) {
        return api.get<ManagedAccountRead[]>(`/me/managed-account-groups/${groupId}/managed-accounts`);
    }

    function createAccount(groupId: number, body: ManagedAccountCreate) {
        return api.post<ManagedAccountCreated>(`/me/managed-account-groups/${groupId}/managed-accounts`, body);
    }

    function bulkCreateAccounts(groupId: number, body: ManagedAccountBulkCreate) {
        return api.post<ManagedAccountBulkCreated>(`/me/managed-account-groups/${groupId}/managed-accounts/bulk`, body);
    }

    function updateAccount(accountId: number, body: ManagedAccountUpdate) {
        return api.patch<ManagedAccountRead>(`/me/managed-accounts/${accountId}`, body);
    }

    function deleteAccount(accountId: number) {
        return api.delete<void>(`/me/managed-accounts/${accountId}`);
    }

    function reissueCode(accountId: number) {
        return api.post<ManagedAccountRead>(`/me/managed-accounts/${accountId}/reissue-code`);
    }

    function openAsAccount(accountId: number) {
        return api.post<UserTokenUpdate>(`/me/managed-accounts/${accountId}/open-as`);
    }

    return {
        listGroups,
        createGroup,
        updateGroup,
        deleteGroup,
        rotateShareToken,
        listAccounts,
        createAccount,
        bulkCreateAccounts,
        updateAccount,
        deleteAccount,
        reissueCode,
        openAsAccount,
    };
}
