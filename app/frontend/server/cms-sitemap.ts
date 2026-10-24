// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
//
// Adds published CMS pages to /sitemap.xml at request time (sitemap.urls in
// nuxt.config.ts only runs at build time). Registered by nuxt.config.ts only
// when CMS_ENABLED, hence outside server/plugins/. The backend answers in the
// sitemap's own source format; a failed fetch is skipped by the module.
export default defineNitroPlugin((nitroApp) => {
    nitroApp.hooks.hook('sitemap:sources', (ctx) => {
        ctx.sources.push({
            context: { name: 'cms', description: 'Published CMS pages' },
            fetch: `${useRuntimeConfig().apiInternal}/cms/sitemap`,
        });
    });
});
