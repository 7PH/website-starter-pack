<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import * as conversationsApi from '~/utils/api/conversations';
import { formatDate, formatTime, initials, markdownSnippet, previewLabel } from '~/utils/formatters';
import { useOpenConversationCount } from '~/config/admin-nav';
import { CORE_CONVERSATION_SUBTYPES, type ConversationSubtypeValue } from '~/config/conversation-subtypes';
import { PROJECT_CONVERSATION_SUBTYPES } from '~/config/conversation-subtypes-ext';

definePageMeta({
    middleware: ['admin'],
});

// The backend can list open conversations or all of them, not closed ones alone.
const segment = ref('open');
const SEGMENTS = [
    { value: 'open', label: 'Open' },
    { value: 'all', label: 'All' },
];
const allSubtypes = [...CORE_CONVERSATION_SUBTYPES, ...PROJECT_CONVERSATION_SUBTYPES];
const subtypeFilter = ref<'all' | ConversationSubtypeValue>('all');
const subtypeOptions = [{ value: 'all' as const, label: 'All types' }, ...allSubtypes];

const { page, limit, offset } = useTableState({ defaultLimit: 50 });

watch([segment, subtypeFilter], () => {
    page.value = 1;
});

const { data: conversationsData, pending } = await useAsyncData<ConversationListResponse>(
    'admin-conversations',
    () =>
        conversationsApi.adminGetConversations({
            includeClosed: segment.value === 'all',
            subtype: subtypeFilter.value !== 'all' ? subtypeFilter.value : undefined,
            limit: limit.value,
            offset: offset.value,
        }),
    { watch: [segment, subtypeFilter, page], server: false },
);

// Keep the sidebar badge in sync with what the admin sees here.
const openCount = useOpenConversationCount();
watch(conversationsData, (data) => {
    if (data && segment.value === 'open' && subtypeFilter.value === 'all') openCount.value = data.total;
});

function subtypeLabel(subtype: string | null | undefined): string {
    return allSubtypes.find((s) => s.value === subtype)?.label ?? 'Contact';
}
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader
            title="Support messages"
            :count="conversationsData?.total"
            description="Conversations started from the contact and bug-report forms."
        />

        <AdminToolbar v-model:segment="segment" :segments="SEGMENTS">
            <USelect
                v-if="allSubtypes.length"
                v-model="subtypeFilter"
                :items="subtypeOptions"
                value-key="value"
                size="lg"
                class="w-44"
            />
        </AdminToolbar>

        <AdminCard :class="{ 'opacity-60': pending }">
            <NuxtLink
                v-for="conversation in conversationsData?.items ?? []"
                :key="conversation.id"
                :to="`/admin/messages/${conversation.id}`"
                class="flex items-start gap-3.5 px-4.5 py-3.5 hover:bg-elevated"
            >
                <span
                    class="flex size-9 shrink-0 items-center justify-center rounded-full bg-elevated text-xs font-extrabold text-toned"
                >
                    {{ initials(previewLabel(conversation.created_by)) || '?' }}
                </span>
                <div class="flex min-w-0 flex-1 flex-col gap-0.5">
                    <div class="flex flex-wrap items-center gap-2">
                        <span class="text-sm font-extrabold text-highlighted">
                            {{ previewLabel(conversation.created_by) }}
                        </span>
                        <UBadge
                            :label="subtypeLabel(conversation.subtype)"
                            :color="conversation.subtype === 'bug_report' ? 'error' : 'neutral'"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="conversation.unread_count"
                            :label="`${conversation.unread_count} unread`"
                            color="primary"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="conversation.is_closed"
                            label="Closed"
                            icon="i-lucide-lock"
                            color="neutral"
                            variant="soft"
                            class="rounded-full"
                        />
                        <span class="flex-1" />
                        <span class="text-xs text-dimmed">
                            {{ formatDate(conversation.updated_at) }} · {{ formatTime(conversation.updated_at) }}
                        </span>
                    </div>
                    <span class="text-sm font-semibold text-highlighted">
                        {{ conversation.subject || '(No subject)' }}
                    </span>
                    <span v-if="conversation.last_message" class="truncate text-[13px] text-muted">
                        {{ markdownSnippet(conversation.last_message.content) }}
                    </span>
                </div>
            </NuxtLink>

            <div
                v-if="!conversationsData?.items.length"
                class="flex flex-col items-center gap-2 px-4.5 py-10 text-sm text-muted"
            >
                <UIcon name="i-lucide-inbox" class="size-6.5 text-dimmed" />
                {{ pending ? 'Loading…' : segment === 'open' ? 'No open conversations.' : 'No conversations yet.' }}
            </div>

            <AdminPagination v-model:page="page" :total="conversationsData?.total ?? 0" :limit="limit" />
        </AdminCard>
    </div>
</template>
