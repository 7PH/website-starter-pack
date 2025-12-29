// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Composable for color mode / dark mode management.
 * Wraps @nuxtjs/color-mode with a simple toggle API.
 */
export function useColorModeToggle() {
    const colorMode = useColorMode();

    const isDark = computed(() => colorMode.value === 'dark');

    const toggle = () => {
        colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark';
    };

    return {
        colorMode,
        isDark,
        toggle,
    };
}
