// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Sign-in by access code for managed accounts.
 *
 * Used by the public picker page (`pages/c/[token].vue`): after the visitor
 * picks their name, they enter their code, and we POST both to /auth/code.
 * The result lands in the same auth store as password/OAuth login, so
 * downstream code (middleware, useApi auth header) just works.
 */

export interface SignInWithCodeArgs {
    managedAccountId: number;
    code: string;
}

export function useAccessCode() {
    const api = useApi();
    const auth = useAuth();

    /**
     * Exchange (managed_account_id, code) for a JWT and persist it.
     * Throws on 401 (invalid code/id) or 429 (rate-limited).
     */
    async function signInWithCode({ managedAccountId, code }: SignInWithCodeArgs): Promise<UserTokenUpdate> {
        const response = await api.post<UserTokenUpdate>('/auth/code', {
            managed_account_id: managedAccountId,
            code,
        });
        auth.saveUserToken(response);
        return response;
    }

    return { signInWithCode };
}
