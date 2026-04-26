<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/**
 * SEO-correct breadcrumb. Always emits `BreadcrumbList` JSON-LD via the
 * underlying `useBreadcrumb` composable.
 *
 * - Visual default: see `BreadcrumbDefault.vue`.
 * - Tweak via slots: `#item` and `#separator`.
 * - Full visual swap: register a replacement under the `'Breadcrumb'` key in
 *   `config/component-overrides.ts`. The override component MUST call
 *   `useBreadcrumb(items)` first thing in `setup` to keep the JSON-LD correct.
 *
 * @example
 * <CommonBreadcrumb :items="[
 *     { label: 'Learn', to: '/app' },
 *     { label: 'Music theory', to: '/app/theory' },
 *     { label: 'Note reading' },
 * ]" />
 */

import BreadcrumbDefault from '~/components/common/BreadcrumbDefault.vue';
import type { BreadcrumbInputItem } from '~/composables/useBreadcrumb';

interface Props {
    items: BreadcrumbInputItem[];
    separator?: string;
}

defineProps<Props>();

const Resolved = useOverridable('Breadcrumb', BreadcrumbDefault);
</script>

<template>
    <component :is="Resolved" :items="items" :separator="separator">
        <template v-for="(_, name) in $slots" #[name]="slotProps">
            <slot :name="name" v-bind="slotProps as object" />
        </template>
    </component>
</template>
