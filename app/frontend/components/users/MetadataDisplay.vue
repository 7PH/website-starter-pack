<!--
Project-specific user custom data read-only display.

Appears in:
  - /admin/users/[id] (the view-mode info grid, alongside User ID / Email / ...)

What to render: read-only blocks for UserCustomData fields you want visible
at a glance. Use the same label+value structure as the siblings in the info
grid so it blends in.

Leave this <div /> empty if your app doesn't need a custom display block.

Example:
    <div class="flex flex-col gap-1">
        <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">User type</span>
        <span class="text-sm text-gray-900 dark:text-gray-100">{{ customData.user_type ?? 'STUDENT' }}</span>
    </div>
    <div v-if="customData.phone" class="flex flex-col gap-1">
        <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Phone</span>
        <span class="text-sm text-gray-900 dark:text-gray-100">{{ customData.phone }}</span>
    </div>
-->

<script lang="ts" setup>
defineProps<{
    customData: UserCustomData;
}>();
</script>

<template>
    <div />
</template>
