// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
// After a client-side navigation focus stays on the clicked link, or falls to <body>: screen readers don't hear the new
// page and the next Tab starts from the top. Move it to the page's heading, or its main area.
export default defineNuxtPlugin((nuxtApp) => {
    // What had focus when the navigation started, while one is pending.
    let focusedBefore: Element | null | undefined;

    // beforeEach, not afterEach: a page with no async setup can finish rendering before afterEach runs.
    useRouter().beforeEach((to, from) => {
        // First load, or only the query/hash changed (eg switching account tabs): nothing to move.
        if (from.matched.length && to.path !== from.path) focusedBefore = document.activeElement;
    });

    function moveFocus(before: Element | null, framesLeft = 60) {
        // During a page transition the old page is still there: wait until the element that had focus is gone.
        if (before && before !== document.body && document.contains(before) && framesLeft > 0) {
            requestAnimationFrame(() => moveFocus(before, framesLeft - 1));
            return;
        }
        const main = document.getElementById('main-content');
        const now = document.activeElement;
        // The new page focused something itself (eg the login form's first field): keep it.
        if (!main || (now && now !== before && now !== document.body && main.contains(now))) return;
        const target = main.querySelector<HTMLElement>('h1') ?? main;
        if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
    }

    nuxtApp.hook('page:finish', () => {
        if (focusedBefore === undefined) return;
        const before = focusedBefore;
        focusedBefore = undefined;
        requestAnimationFrame(() => moveFocus(before));
    });
});
