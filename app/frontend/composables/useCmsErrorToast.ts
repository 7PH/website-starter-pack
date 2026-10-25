// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { cmsErrorKey, cmsLabel } from '~/utils/cms';

/**
 * Toast for a failed request on a CMS screen, always translated (see cmsErrorKey).
 * `fields` lets an error name a field by its label; `onReload` adds a reload button when the page was changed elsewhere.
 *
 * @example
 * const showCmsError = useCmsErrorToast();
 * showCmsError(error, { fields: template.fields, onReload: refresh });
 */
export function useCmsErrorToast() {
    const { t, locale } = useI18n();
    const toast = useToast();

    return (error: unknown, options: { fields?: CmsTemplateField[]; onReload?: () => void } = {}) => {
        const { key, field } = cmsErrorKey(error);
        const fieldDef = options.fields?.find((f) => f.name === field);
        const reload = key === 'cms.pages.changedElsewhere' ? options.onReload : undefined;
        toast.add({
            title: t(key, { field: fieldDef ? cmsLabel(fieldDef.label, locale.value) : field }),
            description: reload ? t('cms.pages.changedElsewhereHelp') : undefined,
            color: key === 'cms.errors.generic' ? 'error' : 'warning',
            // Stays until dismissed: reloading drops unsaved changes, the editor must get the time to decide.
            duration: reload ? 0 : 5000,
            actions: reload ? [{ label: t('cms.pages.reload'), onClick: reload }] : undefined,
        });
    };
}
