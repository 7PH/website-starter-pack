/**
 * Color palettes and design tokens - single source of truth for theming.
 * This file is NOT a starterpack core file - customize it to rebrand your app.
 *
 * Color families:
 * - primary: Main brand color (violet) - buttons, links, focus states
 * - accent: Secondary color (cyan) - highlights, info elements
 * - pop: Special emphasis (fuchsia) - celebrations, special actions
 * - surface: Neutral grays for backgrounds, borders, text
 */

// Surface: Slate (blue-tinted grays for futuristic look)
export const surfacePalette = {
    0: '#ffffff',
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617',
};

// Primary: Violet (brand color)
export const primaryPalette = {
    50: '#f5f3ff',
    100: '#ede9fe',
    200: '#ddd6fe',
    300: '#c4b5fd',
    400: '#a78bfa',
    500: '#8b5cf6',
    600: '#7c3aed',
    700: '#6d28d9',
    800: '#5b21b6',
    900: '#4c1d95',
    950: '#2e1065',
};

// Accent: Cyan (secondary actions, links, info)
export const accentPalette = {
    50: '#ecfeff',
    100: '#cffafe',
    200: '#a5f3fc',
    300: '#67e8f9',
    400: '#22d3ee',
    500: '#06b6d4',
    600: '#0891b2',
    700: '#0e7490',
    800: '#155e75',
    900: '#164e63',
    950: '#083344',
};

// Pop: Fuchsia (special emphasis, celebrations)
export const popPalette = {
    50: '#fdf4ff',
    100: '#fae8ff',
    200: '#f5d0fe',
    300: '#f0abfc',
    400: '#e879f9',
    500: '#d946ef',
    600: '#c026d3',
    700: '#a21caf',
    800: '#86198f',
    900: '#701a75',
    950: '#4a044e',
};

// Brand gradients
export const gradients = {
    brand: 'linear-gradient(135deg, #06b6d4 0%, #8b5cf6 50%, #d946ef 100%)',
    brandSubtle: 'linear-gradient(135deg, rgba(6,182,212,0.1) 0%, rgba(139,92,246,0.1) 50%, rgba(217,70,239,0.1) 100%)',
};

// Glow shadows for vibrant hover effects
export const glowShadows = {
    brand: '0 0 20px rgba(139,92,246,0.35), 0 0 40px rgba(139,92,246,0.2)',
    accent: '0 0 20px rgba(6,182,212,0.35), 0 0 40px rgba(6,182,212,0.2)',
    pop: '0 0 20px rgba(217,70,239,0.35), 0 0 40px rgba(217,70,239,0.2)',
};
