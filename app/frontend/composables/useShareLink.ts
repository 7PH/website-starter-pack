// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Build a public managed-account share URL (/c/<token>) and copy it to the
 * clipboard. Shared by the managed-account-groups list and detail pages.
 */
export function useShareLink() {
    const { t } = useI18n();
    const { showError, showSuccess } = useToastHelpers();

    function shareUrl(token: string) {
        if (typeof window === 'undefined') return '';
        return `${window.location.origin}/c/${token}`;
    }

    async function copyShareLink(token: string) {
        try {
            await navigator.clipboard.writeText(shareUrl(token));
            showSuccess(t('core.managed_accounts.linkCopied'));
        } catch (error) {
            showError(error, 'core.managed_accounts.linkCopyFailed');
        }
    }

    return { shareUrl, copyShareLink };
}
