<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
defineProps<{
    variant?: 'primary' | 'secondary';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
    disabled?: boolean;
}>();
</script>

<template>
    <button :class="['gradient-btn', variant ?? 'primary', size ?? 'md']" :disabled="disabled || loading">
        <span class="btn-content">
            <UIcon v-if="loading" name="i-lucide-loader-2" class="animate-spin" />
            <slot v-else />
        </span>
    </button>
</template>

<style scoped>
@reference "~/assets/css/main.css";

/* Shadow values (inline to ensure availability in scoped styles) */
.gradient-btn {
    --btn-shadow-rest: 0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06);
    --btn-shadow-hover: 0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.02);
    --btn-shadow-glow-brand: 0 0 20px rgba(139,92,246,0.35), 0 0 40px rgba(139,92,246,0.2);
    --btn-shadow-glow-pop: 0 0 20px rgba(217,70,239,0.35), 0 0 40px rgba(217,70,239,0.2);

    @apply relative font-bold uppercase text-white rounded-lg cursor-pointer overflow-hidden;
    @apply inline-flex items-center justify-center;
    box-shadow: var(--btn-shadow-rest);
    transition: transform 300ms cubic-bezier(0.16, 1, 0.3, 1),
                box-shadow 300ms cubic-bezier(0.16, 1, 0.3, 1),
                background-position 400ms ease;
}

/* Hover: float up */
.gradient-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: var(--btn-shadow-hover);
}

/* Active: press down */
.gradient-btn:active:not(:disabled) {
    transform: translateY(0) scale(0.98);
    box-shadow: var(--btn-shadow-rest);
}

.btn-content {
    @apply relative flex items-center justify-center gap-2;
}

/* Sizes */
.gradient-btn.sm {
    @apply px-3 py-1.5 text-xs;
}

.gradient-btn.md {
    @apply px-4 py-2.5 text-xs;
}

.gradient-btn.lg {
    @apply px-5 py-3 text-sm;
}

/* Primary variant: cyan → violet → fuchsia */
.gradient-btn.primary {
    @apply bg-gradient-to-br from-cyan-500 via-violet-500 to-fuchsia-500;
    background-size: 200% 200%;
    background-position: 0% 0%;
}

.gradient-btn.primary:hover:not(:disabled) {
    box-shadow: var(--btn-shadow-glow-brand);
    background-position: 100% 100%;
}

/* Secondary variant: fuchsia → violet */
.gradient-btn.secondary {
    @apply bg-gradient-to-br from-fuchsia-500 to-violet-600;
    background-size: 200% 200%;
    background-position: 0% 0%;
}

.gradient-btn.secondary:hover:not(:disabled) {
    box-shadow: var(--btn-shadow-glow-pop);
    background-position: 100% 100%;
}

/* Disabled state */
.gradient-btn:disabled {
    @apply opacity-50 cursor-not-allowed;
}

/* Focus ring */
.gradient-btn:focus-visible {
    @apply outline-none ring-2 ring-violet-400 ring-offset-2;
}
</style>
