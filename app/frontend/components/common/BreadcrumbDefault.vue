<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/**
 * Default visual implementation for `<Breadcrumb>`. Don't import this directly
 * — use `<CommonBreadcrumb>` which routes through `useOverridable` so sub-apps
 * can swap the visual without losing SEO/a11y wiring.
 */

import type { BreadcrumbInputItem } from '~/composables/useBreadcrumb';

interface Props {
    items: BreadcrumbInputItem[];
    separator?: string;
}

const props = withDefaults(defineProps<Props>(), {
    separator: '/',
});

const { items: decorated } = useBreadcrumb(props.items);
</script>

<template>
    <nav aria-label="Breadcrumb">
        <ol class="flex flex-wrap items-center gap-x-1.5 text-sm text-slate-500 dark:text-slate-400">
            <li
                v-for="(item, index) in decorated"
                :key="index"
                :aria-current="item.ariaCurrent"
                class="flex items-center gap-x-1.5"
            >
                <span v-if="index > 0" aria-hidden="true" class="select-none text-slate-300 dark:text-slate-600">
                    <slot name="separator">{{ separator }}</slot>
                </span>
                <slot name="item" :item="item" :is-last="item.isLast">
                    <NuxtLink
                        v-if="item.to && !item.isLast"
                        :to="item.to"
                        class="hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                    >
                        {{ item.label }}
                    </NuxtLink>
                    <span v-else :class="item.isLast ? 'text-slate-900 dark:text-slate-100 font-medium' : ''">
                        {{ item.label }}
                    </span>
                </slot>
            </li>
        </ol>
    </nav>
</template>
