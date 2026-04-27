// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Resolve the label to show for a user in the UI.
 *
 * The backend already runs the priority ladder (first+last → custom display_name
 * → email) and returns it as `display_label`. This composable adds the i18n
 * fallback for the two cases the backend can't answer: the user has been GDPR-
 * deleted, or every label-source is null.
 */
export function useUserDisplay() {
    const { t } = useI18n();

    function label(
        user:
            | {
                  id: number;
                  auth_method?: string | null;
                  display_label?: string | null;
              }
            | null
            | undefined,
    ): string {
        if (!user) return '';
        if (user.auth_method === 'deleted') {
            return t('core.user.display.deleted');
        }
        return user.display_label ?? t('core.user.display.fallback_id', { id: user.id });
    }

    return { label };
}
