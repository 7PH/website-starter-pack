// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
//
// Remove the `X-Powered-By: Nuxt` header Nitro emits, so responses don't
// disclose the framework. (The backend `Server` header is dropped via uvicorn
// --no-server-header; nginx via server_tokens off.)
export default defineNitroPlugin((nitroApp) => {
    nitroApp.hooks.hook('beforeResponse', (event) => {
        event.node.res.removeHeader('X-Powered-By');
    });
});
