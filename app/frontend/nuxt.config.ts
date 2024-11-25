// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',

  ssr: false,

  devtools: {
    enabled: true
  },

  runtimeConfig: {
    public: {
      apiBase: '', // NUXT_PUBLIC_API_BASE
    }
  },

  modules: ['@pinia/nuxt'],
});