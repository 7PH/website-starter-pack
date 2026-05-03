<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import * as conversationsApi from '~/utils/api/conversations';
import { formatDate, formatTime, previewLabel } from '~/utils/formatters';
import { CORE_CONVERSATION_SUBTYPES, type ConversationSubtypeValue } from '~/config/conversation-subtypes';
import { PROJECT_CONVERSATION_SUBTYPES } from '~/config/conversation-subtypes-ext';

definePageMeta({
    middleware: ['admin'],
});

// Filters
const includeClosed = ref(false);
const allSubtypes = [...CORE_CONVERSATION_SUBTYPES, ...PROJECT_CONVERSATION_SUBTYPES];
const subtypeFilter = ref<'all' | ConversationSubtypeValue>('all');
const subtypeOptions = [{ value: 'all' as const, label: 'All' }, ...allSubtypes];

const { page, limit, offset } = useTableState({ defaultLimit: 50 });

watch([includeClosed, subtypeFilter], () => {
    page.value = 1;
});

const { data: conversationsData, pending } = await useAsyncData<ConversationListResponse>(
    'admin-conversations',
    () =>
        conversationsApi.adminGetConversations({
            includeClosed: includeClosed.value,
            subtype: subtypeFilter.value !== 'all' ? subtypeFilter.value : undefined,
            limit: limit.value,
            offset: offset.value,
        }),
    { watch: [includeClosed, subtypeFilter, page], server: false },
);

const totalPages = computed(() => Math.ceil((conversationsData.value?.total ?? 0) / limit.value));

// Table columns configuration
const columns = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'subject', header: 'Subject' },
    { accessorKey: 'created_by', header: 'From' },
    { accessorKey: 'status', header: 'Status' },
    { accessorKey: 'updated_at', header: 'Last Activity' },
    { accessorKey: 'actions', header: 'Actions' },
];

function getUserDisplay(conversation: ConversationRead): string {
    return previewLabel(conversation.created_by);
}
</script>

<template>
    <div class="page-box">
        <AdminPageBanner />

        <div class="admin-messages">
            <div class="page-header">
                <h1 class="page-title">Support Messages</h1>
                <span class="conversation-count">{{ conversationsData?.total ?? 0 }} total</span>
            </div>

            <!-- Filters -->
            <div class="filters">
                <div v-if="allSubtypes.length" class="filter-item">
                    <label class="filter-label">Subtype</label>
                    <USelect v-model="subtypeFilter" :items="subtypeOptions" value-key="value" class="w-48" />
                </div>
                <div class="flex-1" />
                <UCheckbox v-model="includeClosed" label="Show closed" />
            </div>

            <!-- Conversations Table -->
            <UCard :ui="{ body: 'p-0 sm:p-0' }">
                <UTable :columns="columns" :data="conversationsData?.items ?? []" :loading="pending">
                    <template #id-cell="{ row }">
                        <NuxtLink :to="`/admin/messages/${row.original.id}`" class="conversation-link">
                            #{{ row.original.id }}
                        </NuxtLink>
                    </template>

                    <template #subject-cell="{ row }">
                        <NuxtLink :to="`/admin/messages/${row.original.id}`" class="conversation-link">
                            {{ row.original.subject || '(No subject)' }}
                        </NuxtLink>
                        <p v-if="row.original.last_message" class="message-preview">
                            {{ row.original.last_message.content?.slice(0, 50)
                            }}{{ row.original.last_message.content?.length > 50 ? '...' : '' }}
                        </p>
                    </template>

                    <template #created_by-cell="{ row }">
                        <div class="user-info">
                            <span class="user-name">{{ getUserDisplay(row.original as ConversationRead) }}</span>
                            <span v-if="row.original.created_by" class="user-email">{{
                                row.original.created_by.email
                            }}</span>
                        </div>
                    </template>

                    <template #status-cell="{ row }">
                        <div class="status-badges">
                            <UBadge
                                v-if="(row.original.unread_count ?? 0) > 0"
                                :label="`${row.original.unread_count} unread`"
                                color="primary"
                            />
                            <UBadge v-if="row.original.is_closed" label="Closed" color="neutral" />
                            <UBadge v-else label="Open" color="success" />
                        </div>
                    </template>

                    <template #updated_at-cell="{ row }">
                        <div class="date-cell">
                            <span>{{ formatDate(row.original.updated_at) }}</span>
                            <span class="time">{{ formatTime(row.original.updated_at) }}</span>
                        </div>
                    </template>

                    <template #actions-cell="{ row }">
                        <div class="actions">
                            <UTooltip text="View conversation">
                                <NuxtLink :to="`/admin/messages/${row.original.id}`">
                                    <UButton icon="i-lucide-message-square" color="neutral" variant="ghost" size="xs" />
                                </NuxtLink>
                            </UTooltip>
                            <UTooltip v-if="row.original.created_by" text="View user">
                                <NuxtLink :to="`/admin/users/${row.original.created_by.id}`">
                                    <UButton icon="i-lucide-user" color="neutral" variant="ghost" size="xs" />
                                </NuxtLink>
                            </UTooltip>
                        </div>
                    </template>
                </UTable>

                <!-- Pagination -->
                <div v-if="totalPages > 1" class="pagination-footer">
                    <div class="pagination-info">
                        Showing {{ (page - 1) * limit + 1 }}-{{
                            Math.min(page * limit, conversationsData?.total ?? 0)
                        }}
                        of {{ conversationsData?.total ?? 0 }}
                    </div>
                    <UPagination v-model="page" :total="conversationsData?.total ?? 0" :items-per-page="limit" />
                </div>
            </UCard>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.admin-messages {
    @apply max-w-7xl mx-auto;
}

.page-header {
    @apply flex items-baseline gap-4 mb-6;
}

.page-title {
    @apply text-2xl font-semibold text-gray-900 dark:text-gray-100;
}

.conversation-count {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.filters {
    @apply flex items-end gap-4 mb-4;
}

.filter-item {
    @apply flex flex-col gap-1;
}

.filter-label {
    @apply text-xs font-medium text-gray-500 dark:text-gray-400;
}

.conversation-link {
    @apply text-primary-500 no-underline hover:underline;
}

.message-preview {
    @apply text-xs text-gray-500 dark:text-gray-400 mt-1 truncate max-w-xs;
}

.user-info {
    @apply flex flex-col;
}

.user-name {
    @apply font-medium text-gray-900 dark:text-gray-100;
}

.user-email {
    @apply text-xs text-gray-500 dark:text-gray-400;
}

.status-badges {
    @apply flex flex-wrap gap-1;
}

.date-cell {
    @apply flex flex-col text-sm;
}

.date-cell .time {
    @apply text-xs text-gray-500 dark:text-gray-400;
}

.actions {
    @apply flex gap-1;
}

.pagination-footer {
    @apply flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700;
}

.pagination-info {
    @apply text-sm text-gray-500 dark:text-gray-400;
}
</style>
