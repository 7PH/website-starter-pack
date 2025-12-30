import type { Config } from 'tailwindcss';
import { accentPalette, glowShadows, gradients, popPalette, primaryPalette } from './config/colors';

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
        extend: {
            colors: {
                // Color families - shared with PrimeVue (single source of truth)
                primary: primaryPalette,
                accent: accentPalette,
                pop: popPalette,
            },
            boxShadow: {
                // Elevation system - layered shadows for depth
                'elevation-1': '0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06)',
                'elevation-2': '0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.02)',
                // Glow effects for vibrant hover states
                'glow-brand': glowShadows.brand,
                'glow-accent': glowShadows.accent,
                'glow-pop': glowShadows.pop,
            },
            backgroundImage: {
                // Brand gradients
                'gradient-brand': gradients.brand,
                'gradient-brand-subtle': gradients.brandSubtle,
            },
        },
    },
    plugins: [],
} satisfies Config;
