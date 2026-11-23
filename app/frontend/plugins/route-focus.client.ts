// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
// After a client-side navigation focus stays on the clicked link, or falls to <body>: screen readers don't hear the new
// page and the next Tab starts from the top. Move it to the page's heading, or its main area.
export default defineNuxtPlugin((nuxtApp) => {
    // Set while a navigation is pending: what had focus, and the old page's heading.
    let pending: { focused: Element | null; oldHeading: Element | null } | undefined;

    // beforeEach, not afterEach: a page with no async setup can finish rendering before afterEach runs.
    useRouter().beforeEach((to, from) => {
        // First load, or only the query/hash changed (eg switching account tabs): nothing to move.
        if (!from.matched.length || to.path === from.path) return;
        pending = {
            focused: document.activeElement,
            oldHeading: document.querySelector('#main-content h1'),
        };
    });

    function moveFocus({ focused, oldHeading }: NonNullable<typeof pending>, framesLeft = 60) {
        const now = document.activeElement;
        // The user moved on (tabbed elsewhere) or the new page focused a field itself (eg login): keep it.
        if (now && now !== focused && now !== document.body) return;
        // During a page transition the old page is still there: wait for its heading to go.
        if (oldHeading?.isConnected && framesLeft > 0) {
            requestAnimationFrame(() => moveFocus({ focused, oldHeading }, framesLeft - 1));
            return;
        }
        const main = document.getElementById('main-content');
        if (!main) return;
        const target = main.querySelector<HTMLElement>('h1') ?? main;
        if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
    }

    nuxtApp.hook('page:finish', () => {
        if (!pending) return;
        const navigation = pending;
        pending = undefined;
        requestAnimationFrame(() => moveFocus(navigation));
    });
});
