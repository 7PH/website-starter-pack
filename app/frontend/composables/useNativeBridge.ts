// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
/**
 * Single entry point for talking to a native shell (Capacitor wrapper).
 *
 * On the web, returns a no-op stub — callers don't branch on platform.
 * In a Capacitor wrapper, the app's client plugin assigns a real
 * implementation to `window.__nativeBridge` before any composable runs.
 *
 * Apps that need additional methods (haptic, native audio, push, ...)
 * extend this interface via TypeScript module augmentation — see README.
 */

export interface NativeBridge {
    isNative(): boolean;
    /** Open a URL in the native browser (Chrome custom tab / SFSafariViewController), not the in-app webview. */
    openExternal(url: string): Promise<void>;
}

declare global {
    interface Window {
        __nativeBridge?: NativeBridge;
    }
}

const webStub: NativeBridge = {
    isNative: () => false,
    async openExternal(url) {
        if (import.meta.client) window.open(url, '_blank');
    },
};

export function useNativeBridge(): NativeBridge {
    if (import.meta.client && window.__nativeBridge) {
        return window.__nativeBridge;
    }
    return webStub;
}
