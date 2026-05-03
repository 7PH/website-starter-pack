<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import * as conversationsApi from '~/utils/api/conversations';
import { formatDate, formatTime, previewLabel } from '~/utils/formatters';

definePageMeta({
    middleware: ['admin'],
    layout: 'fullheight',
});

const route = useRoute();
const router = useRouter();
const { showSuccess, showError } = useToastHelpers();
const modal = useModalStore();
const auth = useAuth();

const conversationId = computed(() => Number(route.params.id));

const {
    data: conversation,
    pending,
    refresh,
} = await useAsyncData<ConversationDetail>(
    `admin-conversation-${conversationId.value}`,
    () => conversationsApi.adminGetConversation(conversationId.value),
    { server: false },
);

// New message
const newMessage = ref('');
const sending = ref(false);
const composeMode = ref<'write' | 'preview'>('write');

async function sendMessage() {
    if (!newMessage.value.trim()) return;

    sending.value = true;
    try {
        await conversationsApi.adminSendMessage(conversationId.value, {
            content: newMessage.value,
        });

        newMessage.value = '';
        await refresh();

        showSuccess('Message sent');

        // Scroll to bottom after sending
        await nextTick();
        scrollToBottom();
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        sending.value = false;
    }
}

// Close/Reopen actions
const actionPending = ref(false);

async function setClosed(closed: boolean) {
    actionPending.value = true;
    try {
        await conversationsApi.adminUpdateConversation(conversationId.value, { is_closed: closed });
        await refresh();
        showSuccess(closed ? 'Conversation closed' : 'Conversation reopened');
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        actionPending.value = false;
    }
}

async function closeConversation() {
    const confirmed = await modal.open('confirm', {
        title: 'Close Conversation',
        message: 'Are you sure you want to close this conversation?',
        confirmText: 'Close',
        confirmColor: 'warning',
    });
    if (confirmed) await setClosed(true);
}

const reopenConversation = () => setClosed(false);

const { container: messagesContainer, scrollToBottom } = useScrollToBottom(() => conversation.value?.messages?.length);

function isOwnMessage(message: MessageRead): boolean {
    return message.sender_id === auth.user?.id;
}

function getSenderName(message: MessageRead): string {
    return previewLabel(message.sender);
}

function getUserDisplay(conv: ConversationDetail): string {
    return previewLabel(conv.created_by);
}
</script>

<template>
    <div class="page-box admin-conversation-page">
        <AdminPageBanner />

        <div class="admin-conversation">
            <!-- Back link -->
            <NuxtLink to="/admin/messages" class="back-link">
                <UIcon name="i-lucide-arrow-left" />
                Back to Messages
            </NuxtLink>

            <div v-if="pending" class="loading-state">
                <LoadingSkeleton class="h-96" />
            </div>

            <div v-else-if="!conversation" class="error-state">
                <p>Conversation not found</p>
                <UButton label="Back to Messages" @click="router.push('/admin/messages')" />
            </div>

            <template v-else>
                <!-- Conversation Header -->
                <div class="conversation-header">
                    <div class="header-main">
                        <h1 class="conversation-subject">
                            {{ conversation.subject || '(No subject)' }}
                        </h1>
                        <div class="conversation-meta">
                            <span
                                >From: <strong>{{ getUserDisplay(conversation) }}</strong></span
                            >
                            <span v-if="conversation.created_by">
                                (<NuxtLink :to="`/admin/users/${conversation.created_by.id}`" class="user-link">{{
                                    conversation.created_by.email
                                }}</NuxtLink
                                >)
                            </span>
                            <span class="separator">|</span>
                            <span>Created: {{ formatDate(conversation.created_at) }}</span>
                        </div>
                    </div>
                    <div class="header-actions">
                        <UBadge v-if="conversation.is_closed" label="Closed" color="neutral" size="lg" />
                        <UBadge v-else label="Open" color="success" size="lg" />

                        <UButton
                            v-if="conversation.is_closed"
                            icon="i-lucide-unlock"
                            label="Reopen"
                            color="primary"
                            variant="outline"
                            :loading="actionPending"
                            @click="reopenConversation"
                        />
                        <UButton
                            v-else
                            icon="i-lucide-lock"
                            label="Close"
                            color="warning"
                            variant="outline"
                            :loading="actionPending"
                            @click="closeConversation"
                        />
                    </div>
                </div>

                <!-- Messages -->
                <UCard :ui="{ body: 'p-0 sm:p-0 flex-1 min-h-0 flex flex-col' }" class="flex-1 min-h-0 flex flex-col">
                    <div ref="messagesContainer" class="messages-container">
                        <div
                            v-for="message in conversation.messages"
                            :key="message.id"
                            class="message"
                            :class="{
                                'admin-message': message.is_admin_response,
                                'user-message': !message.is_admin_response,
                            }"
                        >
                            <div class="message-bubble">
                                <div class="message-header">
                                    <span class="message-sender">
                                        {{ getSenderName(message) }}
                                        <UBadge
                                            v-if="message.is_admin_response"
                                            label="Admin"
                                            color="info"
                                            size="xs"
                                            class="ml-1"
                                        />
                                    </span>
                                    <span class="message-time"
                                        >{{ formatDate(message.created_at) }} {{ formatTime(message.created_at) }}</span
                                    >
                                </div>
                                <MessageContent :content="message.content" />
                            </div>
                        </div>

                        <div v-if="!conversation.messages?.length" class="no-messages">No messages yet</div>
                    </div>

                    <!-- Message Input -->
                    <div v-if="!conversation.is_closed" class="message-input-area">
                        <div class="compose-toolbar">
                            <UButton
                                size="xs"
                                :variant="composeMode === 'write' ? 'soft' : 'ghost'"
                                label="Write"
                                @click="composeMode = 'write'"
                            />
                            <UButton
                                size="xs"
                                :variant="composeMode === 'preview' ? 'soft' : 'ghost'"
                                label="Preview"
                                :disabled="!newMessage.trim()"
                                @click="composeMode = 'preview'"
                            />
                        </div>
                        <UTextarea
                            v-show="composeMode === 'write'"
                            v-model="newMessage"
                            placeholder="Type your reply... (Ctrl+Enter to send)"
                            :rows="3"
                            class="message-input"
                            @keydown.ctrl.enter="sendMessage"
                            @keydown.meta.enter="sendMessage"
                        />
                        <div v-show="composeMode === 'preview'" class="message-preview">
                            <MessageContent :content="newMessage" />
                        </div>
                        <div class="input-actions">
                            <UButton
                                icon="i-lucide-send"
                                label="Send Reply"
                                :loading="sending"
                                :disabled="!newMessage.trim()"
                                @click="sendMessage"
                            />
                        </div>
                    </div>

                    <div v-else class="closed-notice">
                        <UIcon name="i-lucide-lock" />
                        This conversation is closed. Reopen it to send messages.
                    </div>
                </UCard>
            </template>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.admin-conversation-page {
    @apply flex flex-col flex-1 min-h-0;
}

.admin-conversation {
    @apply w-full flex flex-col flex-1 min-h-0;
}

.back-link {
    @apply flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 no-underline mb-4;
}

.loading-state,
.error-state {
    @apply flex flex-col items-center justify-center py-12 gap-4;
}

.conversation-header {
    @apply flex items-start justify-between mb-4 gap-4;
}

.header-main {
    @apply flex-1;
}

.conversation-subject {
    @apply text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1;
}

.conversation-meta {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.user-link {
    @apply text-primary-500 hover:underline;
}

.separator {
    @apply mx-2;
}

.header-actions {
    @apply flex items-center gap-2;
}

.messages-container {
    @apply p-4 flex-1 min-h-0 overflow-y-auto space-y-4;
}

.message {
    @apply flex;
}

.user-message {
    @apply justify-start;
}

.admin-message {
    @apply justify-end;
}

.message-bubble {
    @apply max-w-[75%] rounded-lg p-3;
    @apply bg-gray-100 dark:bg-gray-800;
}

.admin-message .message-bubble {
    @apply bg-primary-100 dark:bg-primary-900/30;
}

.message-header {
    @apply flex items-center justify-between gap-4 mb-1 flex-wrap;
}

.message-sender {
    @apply text-xs font-medium text-gray-700 dark:text-gray-300 flex items-center;
}

.message-time {
    @apply text-xs text-gray-500 dark:text-gray-400;
}

.no-messages {
    @apply text-center text-gray-500 dark:text-gray-400 py-8;
}

.message-input-area {
    @apply p-4 border-t border-gray-200 dark:border-gray-700 space-y-3;
}

.compose-toolbar {
    @apply flex gap-1;
}

.message-input {
    @apply w-full;
}

.message-preview {
    @apply w-full min-h-[5rem] rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-3;
}

.input-actions {
    @apply flex justify-end;
}

.closed-notice {
    @apply flex items-center justify-center gap-2 p-4 text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700;
}
</style>
