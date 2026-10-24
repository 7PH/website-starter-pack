<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
import { RICH_TEXT_CLASS } from '~/utils/cms';

defineProps<{ html: string }>();
</script>

<template>
    <!-- eslint-disable-next-line vue/no-v-html -- sanitized server-side on save (helpers/sanitize.py:sanitize_rich_text) -->
    <div :class="RICH_TEXT_CLASS" v-html="html" />
</template>
