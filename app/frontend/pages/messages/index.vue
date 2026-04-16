<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import * as conversationsApi from '~/utils/api/conversations';
import MessagesPageActionsDefault from '~/components/messages/PageActions.vue';

definePageMeta({
    middleware: 'auth',
    auth: true,
});

// Overridable components - sub-apps can replace these via config/component-overrides.ts
const MessagesPageActions = useOverridable('MessagesPageActions', MessagesPageActionsDefault);

const { t } = useI18n();
const toast = useToast();
const router = useRouter();

// Filters
const includeClosed = ref(false);

// Pagination
const page = ref(1);
const itemsPerPage = 20;

// Reset page when filters change
watch([includeClosed], () => {
    page.value = 1;
});

const {
    data: conversationsData,
    pending,
    refresh,
} = await useAsyncData<ConversationListResponse>(
    'user-conversations',
    () =>
        conversationsApi.getConversations({
            includeClosed: includeClosed.value,
            limit: itemsPerPage,
            offset: (page.value - 1) * itemsPerPage,
        }),
    { watch: [includeClosed, page], server: false },
);

const totalPages = computed(() => Math.ceil((conversationsData.value?.total ?? 0) / itemsPerPage));

// New conversation modal
const showNewConversation = ref(false);
const newConversation = ref({
    subject: '',
    content: '',
});
const creating = ref(false);

async function createConversation() {
    if (!newConversation.value.content.trim()) {
        toast.add({
            title: t('core.messages.error'),
            description: t('core.messages.messageRequired'),
            color: 'error',
        });
        return;
    }

    creating.value = true;
    try {
        const conversation = await conversationsApi.createConversation({
            subject: newConversation.value.subject ?? '',
            content: newConversation.value.content,
        });

        toast.add({
            title: t('core.messages.success'),
            description: t('core.messages.conversationCreated'),
            color: 'success',
        });

        showNewConversation.value = false;
        newConversation.value = { subject: '', content: '' };

        // Navigate to the new conversation
        router.push(`/messages/${conversation.id}`);
    } catch {
        toast.add({
            title: t('core.messages.error'),
            description: t('core.messages.createFailed'),
            color: 'error',
        });
    } finally {
        creating.value = false;
    }
}

function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
}

function formatTime(dateStr: string | null | undefined): string {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function truncateMessage(content: string | undefined, maxLength = 60): string {
    if (!content) return '';
    if (content.length <= maxLength) return content;
    return content.slice(0, maxLength) + '...';
}
</script>

<template>
    <div class="page-box">
        <UiPageTitleBanner compact>
            {{ t('core.messages.title') }}
            <template #subtitle>
                {{ t('core.messages.subtitle') }}
            </template>
        </UiPageTitleBanner>

        <div class="messages-page">
            <!-- Header with actions -->
            <MessagesPageActions
                v-model:include-closed="includeClosed"
                :total-count="conversationsData?.total ?? 0"
                @new-conversation="showNewConversation = true"
            />

            <!-- Conversations List -->
            <UCard :ui="{ body: 'p-0 sm:p-0' }">
                <div v-if="pending" class="loading-state">
                    <LoadingSkeleton class="h-16" />
                    <LoadingSkeleton class="h-16" />
                    <LoadingSkeleton class="h-16" />
                </div>

                <div v-else-if="!conversationsData?.items?.length" class="empty-state">
                    <UIcon name="i-lucide-message-square" class="empty-icon" />
                    <p class="empty-text">{{ t('core.messages.noConversations') }}</p>
                    <UButton :label="t('core.messages.startConversation')" @click="showNewConversation = true" />
                </div>

                <div v-else class="conversation-list">
                    <NuxtLink
                        v-for="conversation in conversationsData.items"
                        :key="conversation.id"
                        :to="`/messages/${conversation.id}`"
                        class="conversation-item"
                        :class="{ 'is-closed': conversation.is_closed }"
                    >
                        <div class="conversation-main">
                            <div class="conversation-header">
                                <span class="conversation-subject">
                                    {{ conversation.subject || t('core.messages.noSubject') }}
                                </span>
                                <div class="conversation-badges">
                                    <UBadge
                                        v-if="(conversation.unread_count ?? 0) > 0"
                                        :label="String(conversation.unread_count)"
                                        color="primary"
                                    />
                                    <UBadge
                                        v-if="conversation.is_closed"
                                        :label="t('core.messages.closed')"
                                        color="neutral"
                                    />
                                </div>
                            </div>
                            <p v-if="conversation.last_message" class="conversation-preview">
                                {{ truncateMessage(conversation.last_message.content) }}
                            </p>
                        </div>
                        <div class="conversation-meta">
                            <span class="conversation-date">{{ formatDate(conversation.updated_at) }}</span>
                            <span class="conversation-time">{{ formatTime(conversation.updated_at) }}</span>
                        </div>
                    </NuxtLink>
                </div>

                <!-- Pagination -->
                <div v-if="totalPages > 1" class="pagination-footer">
                    <div class="pagination-info">
                        {{ t('core.messages.showing') }} {{ (page - 1) * itemsPerPage + 1 }}-{{
                            Math.min(page * itemsPerPage, conversationsData?.total ?? 0)
                        }}
                        {{ t('core.messages.of') }} {{ conversationsData?.total ?? 0 }}
                    </div>
                    <UPagination v-model="page" :total="conversationsData?.total ?? 0" :items-per-page="itemsPerPage" />
                </div>
            </UCard>
        </div>

        <!-- New Conversation Modal -->
        <UModal v-model:open="showNewConversation">
            <template #content>
                <UCard>
                    <template #header>
                        <UiModalHeader
                            :title="t('core.messages.newConversation')"
                            @close="showNewConversation = false"
                        />
                    </template>

                    <div class="modal-form">
                        <UFormField :label="t('core.messages.subjectLabel')">
                            <UInput
                                v-model="newConversation.subject"
                                :placeholder="t('core.messages.subjectPlaceholder')"
                                class="w-full"
                            />
                        </UFormField>

                        <UFormField :label="t('core.messages.messageLabel')" required>
                            <UTextarea
                                v-model="newConversation.content"
                                :placeholder="t('core.messages.messagePlaceholder')"
                                :rows="5"
                                class="w-full"
                            />
                        </UFormField>
                    </div>

                    <template #footer>
                        <UiFormActions>
                            <UButton
                                color="neutral"
                                variant="outline"
                                :label="t('core.common.cancel')"
                                @click="showNewConversation = false"
                            />
                            <UButton :label="t('core.messages.send')" :loading="creating" @click="createConversation" />
                        </UiFormActions>
                    </template>
                </UCard>
            </template>
        </UModal>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.loading-state {
    @apply p-4 space-y-2;
}

.empty-state {
    @apply flex flex-col items-center justify-center py-12 gap-4;
}

.empty-icon {
    @apply w-12 h-12 text-gray-400;
}

.empty-text {
    @apply text-gray-500 dark:text-gray-400;
}

.conversation-list {
    @apply divide-y divide-gray-200 dark:divide-gray-700;
}

.conversation-item {
    @apply flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer no-underline;
}

.conversation-item.is-closed {
    @apply opacity-60;
}

.conversation-main {
    @apply flex-1 min-w-0;
}

.conversation-header {
    @apply flex items-center gap-2 mb-1;
}

.conversation-subject {
    @apply font-medium text-gray-900 dark:text-gray-100 truncate;
}

.conversation-badges {
    @apply flex gap-1 flex-shrink-0;
}

.conversation-preview {
    @apply text-sm text-gray-500 dark:text-gray-400 truncate;
}

.conversation-meta {
    @apply flex flex-col items-end text-xs text-gray-500 dark:text-gray-400 ml-4 flex-shrink-0;
}

.pagination-footer {
    @apply flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700;
}

.pagination-info {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.modal-form {
    @apply space-y-4;
}
</style>
