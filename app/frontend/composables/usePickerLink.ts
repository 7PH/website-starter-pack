// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Persist the public-picker URL in localStorage so a managed account can
 * return to their sign-in page without needing the original message/QR code.
 *
 * Used by:
 *   - `pages/c/[token].vue` writes the entry after the visitor lands
 *   - `pages/login.vue` (or the homepage) reads it to render a "Resume sign-in" card
 */

const STORAGE_KEY = 'lastSignInLink';

export interface PickerLinkEntry {
    /** The public share_token, used to rebuild the /c/<token> URL. */
    token: string;
    /** Last picked managed_account_id, so we can pre-select the name on return. */
    lastAccountId: number | null;
    /** Group name we showed the last time, just for nicer UX on the resume card. */
    groupName: string | null;
    /** Unix ms of last visit. */
    savedAt: number;
}

export function usePickerLink() {
    function isAvailable() {
        return typeof window !== 'undefined' && !!window.localStorage;
    }

    function read(): PickerLinkEntry | null {
        if (!isAvailable()) return null;
        try {
            const raw = window.localStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            const parsed = JSON.parse(raw) as PickerLinkEntry;
            if (!parsed?.token) return null;
            return parsed;
        } catch {
            return null;
        }
    }

    function write(entry: Omit<PickerLinkEntry, 'savedAt'>) {
        if (!isAvailable()) return;
        const payload: PickerLinkEntry = { ...entry, savedAt: Date.now() };
        try {
            window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
        } catch {
            // localStorage can be full or disabled; silently degrade.
        }
    }

    function clear() {
        if (!isAvailable()) return;
        try {
            window.localStorage.removeItem(STORAGE_KEY);
        } catch {
            // ignore
        }
    }

    return { read, write, clear };
}
