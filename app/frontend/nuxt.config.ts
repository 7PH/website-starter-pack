// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  runtimeConfig: {
    public: {
      apiBase: '', // NUXT_PUBLIC_API_BASE
    }
  },
  modules: ['@pinia/nuxt', '@nuxt/ui'],
  css: ['~/assets/css/main.css']
});
