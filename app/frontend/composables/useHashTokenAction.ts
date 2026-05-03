// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Read a token from the URL fragment (#token), run an async confirm action,
 * and expose loading/success/error state.
 *
 * Used by the email-verification and email-change pages, both of which land
 * the user on a route with the token in the fragment so it doesn't leak to
 * server access logs.
 */
export function useHashTokenAction(opts: {
    action: (token: string) => Promise<boolean>;
    noTokenMessage: string;
    invalidMessage: string;
    onSuccess?: () => void;
}) {
    const status = ref<'loading' | 'success' | 'error'>('loading');
    const errorMessage = ref('');

    onMounted(async () => {
        const hash = window.location.hash;
        const token = hash ? hash.substring(1) : null;
        if (!token) {
            status.value = 'error';
            errorMessage.value = opts.noTokenMessage;
            return;
        }
        const success = await opts.action(token);
        if (success) {
            status.value = 'success';
            opts.onSuccess?.();
        } else {
            status.value = 'error';
            errorMessage.value = opts.invalidMessage;
        }
    });

    return { status, errorMessage };
}
