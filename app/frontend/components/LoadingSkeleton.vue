<script setup lang="ts">
// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

interface Props {
    /** Number of skeleton rows to show */
    rows?: number;
    /** Variant: 'text', 'card', 'table', 'avatar' */
    variant?: 'text' | 'card' | 'table' | 'avatar';
}

withDefaults(defineProps<Props>(), {
    rows: 3,
    variant: 'text',
});
</script>

<template>
    <!-- Text variant - simple lines -->
    <div v-if="variant === 'text'" class="space-y-3">
        <div
            v-for="i in rows"
            :key="i"
            class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
            :class="{ 'w-3/4': i === rows }"
        />
    </div>

    <!-- Card variant - card with content -->
    <div v-else-if="variant === 'card'" class="space-y-4">
        <div
            v-for="i in rows"
            :key="i"
            class="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
        >
            <div class="flex items-center space-x-4">
                <div class="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
                <div class="flex-1 space-y-2">
                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4" />
                    <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2" />
                </div>
            </div>
        </div>
    </div>

    <!-- Table variant - table rows -->
    <div v-else-if="variant === 'table'" class="space-y-2">
        <div
            v-for="i in rows"
            :key="i"
            class="flex items-center space-x-4 py-3 border-b border-gray-200 dark:border-gray-700"
        >
            <div class="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            <div class="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            <div class="w-24 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            <div class="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
    </div>

    <!-- Avatar variant - circular avatars with text -->
    <div v-else-if="variant === 'avatar'" class="space-y-3">
        <div v-for="i in rows" :key="i" class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
            <div class="flex-1 space-y-1.5">
                <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/3" />
                <div class="h-2.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/4" />
            </div>
        </div>
    </div>
</template>
