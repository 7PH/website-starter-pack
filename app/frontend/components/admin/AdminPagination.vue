<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Footer row of a paginated AdminCard: "Showing 1–50 of 120" with Previous / Next.
const props = defineProps<{
    total: number;
    limit: number;
}>();

const page = defineModel<number>('page', { required: true });
const lastPage = computed(() => Math.max(1, Math.ceil(props.total / props.limit)));
</script>

<template>
    <div v-if="total" class="flex items-center justify-between gap-3 px-4.5 py-2.5 text-[13px] text-muted">
        <span>Showing {{ (page - 1) * limit + 1 }}–{{ Math.min(page * limit, total) }} of {{ total }}</span>
        <div v-if="lastPage > 1" class="flex gap-1.5">
            <UButton
                label="Previous"
                color="neutral"
                variant="outline"
                size="sm"
                :disabled="page <= 1"
                @click="page--"
            />
            <UButton
                label="Next"
                color="neutral"
                variant="outline"
                size="sm"
                :disabled="page >= lastPage"
                @click="page++"
            />
        </div>
    </div>
</template>
