import type { Config } from 'tailwindcss';

export default {
    darkMode: 'class',
    content: [
        './components/**/*.{vue,js,ts}',
        './layouts/**/*.vue',
        './pages/**/*.vue',
        './composables/**/*.{js,ts}',
        './plugins/**/*.{js,ts}',
        './app.vue',
    ],
    theme: {
        extend: {},
    },
    plugins: [],
} satisfies Config;
