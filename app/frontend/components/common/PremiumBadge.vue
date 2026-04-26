<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/**
 * Decorative gold lock badge marking content as premium.
 *
 * Pairs visually with `<PremiumGate>` but is independent: this component
 * does not check entitlement and does not handle clicks. Place it next
 * to a title, card, or list item to signal that the target is premium.
 * If you want the badge to be clickable, wrap it: `<NuxtLink to="/premium"><PremiumBadge /></NuxtLink>`.
 */

type Size = 'sm' | 'md' | 'lg';

interface Props {
    size?: Size;
    /** Tooltip text. Defaults to the `core.premium.gate.badgeTooltip` i18n key. */
    tooltip?: string;
}

const props = withDefaults(defineProps<Props>(), {
    size: 'md',
    tooltip: undefined,
});

const { t } = useI18n();

const tooltipText = computed(() => props.tooltip ?? t('core.premium.gate.badgeTooltip'));

const sizeClasses: Record<Size, { box: string; icon: string }> = {
    sm: { box: 'w-5 h-5', icon: 'w-3 h-3' },
    md: { box: 'w-7 h-7', icon: 'w-4 h-4' },
    lg: { box: 'w-9 h-9', icon: 'w-5 h-5' },
};
</script>

<template>
    <UTooltip :text="tooltipText">
        <span
            :class="[
                sizeClasses[size].box,
                'inline-flex items-center justify-center rounded-full bg-gradient-to-br from-amber-300 to-amber-500 text-white shadow-sm ring-1 ring-amber-600/20',
            ]"
            :aria-label="tooltipText"
            role="img"
        >
            <UIcon name="i-lucide-lock" :class="sizeClasses[size].icon" />
        </span>
    </UTooltip>
</template>
