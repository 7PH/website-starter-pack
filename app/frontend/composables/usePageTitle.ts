// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Browser tab title "Page · App", so open tabs can be told apart. Without it a page shows the bare app name.
 *
 * @example
 * usePageTitle(() => t('core.messages.title'));
 */
export function usePageTitle(title: MaybeRefOrGetter<string | undefined>) {
    const appName = useRuntimeConfig().public.appName as string;
    useHead({
        title: () => {
            const page = toValue(title);
            return page ? `${page} · ${appName}` : appName;
        },
    });
}
