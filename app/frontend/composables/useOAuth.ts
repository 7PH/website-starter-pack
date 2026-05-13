// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
/**
 * OAuth composable for handling Google OAuth authentication.
 * Provides methods to initiate OAuth flow and handle callbacks.
 */

// Storage key for OAuth state (CSRF protection)
const OAUTH_STATE_KEY = 'oauth_state';

export function useOAuth() {
    const api = useApi();
    const auth = useAuth();
    const { showError } = useToastHelpers();

    /**
     * Check if OAuth is enabled and which providers are available.
     */
    async function getOAuthStatusResponse(): Promise<OAuthStatusResponse> {
        try {
            return await api.get<OAuthStatusResponse>('/oauth/status');
        } catch {
            return { enabled: false, providers: [] };
        }
    }

    /**
     * Check if Google OAuth is available.
     */
    async function isGoogleOAuthEnabled(): Promise<boolean> {
        const status = await getOAuthStatusResponse();
        return status.enabled && status.providers.includes('google');
    }

    /**
     * Start the Google OAuth flow.
     *
     * On the web, the current tab redirects to Google. Inside a Capacitor
     * wrapper, Google opens in the native browser (Chrome custom tab /
     * SFSafariViewController) — Google blocks OAuth in embedded webviews
     * (`disallowed_useragent`). The wrapper is expected to forward the
     * deep-link callback to `/oauth/callback?code=...&state=...` in the
     * webview, where `handleOAuthCallback` takes over.
     */
    async function startGoogleOAuth(): Promise<void> {
        try {
            const response = await api.get<OAuthUrlResponse>('/oauth/google/url');

            // Save state to localStorage for CSRF validation on callback
            if (import.meta.client) {
                localStorage.setItem(OAUTH_STATE_KEY, response.state);
            }

            const bridge = useNativeBridge();
            if (bridge.isNative()) {
                await bridge.openExternal(response.url);
                return;
            }
            window.location.href = response.url;
        } catch (error) {
            showError(error, 'core.oauth.errorStarting');
        }
    }

    /**
     * Handle the OAuth callback.
     * Validates the state parameter, exchanges the code for a token,
     * and logs the user in.
     *
     * @param code - Authorization code from Google
     * @param state - State parameter for CSRF validation
     * @returns true if login was successful
     */
    async function handleOAuthCallback(code: string, state: string): Promise<boolean> {
        // Validate state parameter (CSRF protection)
        if (import.meta.client) {
            const savedState = localStorage.getItem(OAUTH_STATE_KEY);
            if (!savedState || savedState !== state) {
                showError(new Error('Invalid state parameter'), 'core.oauth.errorCallback');
                return false;
            }
            // Clear the saved state
            localStorage.removeItem(OAUTH_STATE_KEY);
        }

        try {
            const body: OAuthCallbackRequest = { code, state };
            const response = await api.post<UserTokenUpdate>('/oauth/google/callback', body);

            // Store the token and user data
            auth.saveUserToken(response);

            return true;
        } catch (error) {
            showError(error, 'core.oauth.errorCallback');
            return false;
        }
    }

    /**
     * Clear any pending OAuth state (useful when user cancels flow).
     */
    function clearOAuthState(): void {
        if (import.meta.client) {
            localStorage.removeItem(OAUTH_STATE_KEY);
        }
    }

    return {
        getOAuthStatusResponse,
        isGoogleOAuthEnabled,
        startGoogleOAuth,
        handleOAuthCallback,
        clearOAuthState,
    };
}
