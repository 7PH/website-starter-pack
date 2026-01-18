<script lang="ts" setup>
import * as conversationsApi from '~/utils/api/conversations';

definePageMeta({
    middleware: 'auth',
    auth: true,
    layout: 'fullheight',
});

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const toast = useToast();
const auth = useAuth();

const conversationId = computed(() => Number(route.params.id));

const {
    data: conversation,
    pending,
    refresh,
} = await useAsyncData<ConversationDetail>(
    `conversation-${conversationId.value}`,
    () => conversationsApi.getConversation(conversationId.value),
    { server: false },
);

// New message
const newMessage = ref('');
const sending = ref(false);

async function sendMessage() {
    if (!newMessage.value.trim()) return;
    if (conversation.value?.is_closed) {
        toast.add({
            title: t('core.messages.error'),
            description: t('core.messages.conversationClosed'),
            color: 'error',
        });
        return;
    }

    sending.value = true;
    try {
        await conversationsApi.sendMessage(conversationId.value, {
            content: newMessage.value,
        });

        newMessage.value = '';
        await refresh();

        // Scroll to bottom after sending
        await nextTick();
        scrollToBottom();
    } catch {
        toast.add({
            title: t('core.messages.error'),
            description: t('core.messages.sendFailed'),
            color: 'error',
        });
    } finally {
        sending.value = false;
    }
}

// Scroll handling
const messagesContainer = ref<HTMLElement | null>(null);

function scrollToBottom() {
    if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
}

// Scroll to bottom on load
onMounted(() => {
    nextTick(() => scrollToBottom());
});

// Watch for conversation changes and scroll to bottom
watch(
    () => conversation.value?.messages?.length,
    () => {
        nextTick(() => scrollToBottom());
    },
);

function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString();
}

function formatTime(dateStr: string | null | undefined): string {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function isOwnMessage(message: MessageRead): boolean {
    return message.sender_id === auth.user?.id;
}

function getSenderName(message: MessageRead): string {
    if (message.is_admin_response) {
        return t('core.messages.supportTeam');
    }
    if (message.sender) {
        const name = [message.sender.first_name, message.sender.last_name].filter(Boolean).join(' ');
        return name || message.sender.email;
    }
    return t('core.messages.unknown');
}
</script>

<template>
    <div class="page-box conversation-page-wrapper">
        <!-- Header -->
        <div class="conversation-top">
            <NuxtLink to="/messages" class="back-link">
                <UIcon name="i-lucide-arrow-left" />
                {{ t('core.messages.backToMessages') }}
            </NuxtLink>

            <div v-if="conversation" class="conversation-header">
                <div class="header-info">
                    <h1 class="conversation-subject">
                        {{ conversation.subject || t('core.messages.noSubject') }}
                    </h1>
                    <span class="conversation-date">
                        {{ t('core.messages.started') }} {{ formatDate(conversation.created_at) }}
                    </span>
                </div>
                <div class="header-badges">
                    <UBadge v-if="conversation.is_closed" :label="t('core.messages.closed')" color="neutral" />
                </div>
            </div>
        </div>

        <!-- Loading/Error states -->
        <div v-if="pending" class="loading-state">
            <LoadingSkeleton class="h-96 w-full max-w-3xl" />
        </div>

        <div v-else-if="!conversation" class="error-state">
            <p>{{ t('core.messages.conversationNotFound') }}</p>
            <UButton :label="t('core.messages.backToMessages')" @click="router.push('/messages')" />
        </div>

        <!-- Messages Area -->
        <template v-else>
            <div ref="messagesContainer" class="messages-container">
                <div class="messages-inner">
                    <div
                        v-for="message in conversation.messages"
                        :key="message.id"
                        class="message"
                        :class="{ 'own-message': isOwnMessage(message) }"
                    >
                        <div class="message-bubble">
                            <div class="message-header">
                                <span class="message-sender">{{ getSenderName(message) }}</span>
                                <span class="message-time">{{ formatTime(message.created_at) }}</span>
                            </div>
                            <div class="message-content">{{ message.content }}</div>
                        </div>
                    </div>

                    <div v-if="!conversation.messages?.length" class="no-messages">
                        {{ t('core.messages.noMessagesYet') }}
                    </div>
                </div>
            </div>

            <!-- Message Input -->
            <div v-if="!conversation.is_closed" class="message-input-area">
                <div class="input-inner">
                    <UTextarea
                        v-model="newMessage"
                        :placeholder="t('core.messages.typeMessage')"
                        :rows="2"
                        class="message-input"
                        @keydown.ctrl.enter="sendMessage"
                        @keydown.meta.enter="sendMessage"
                    />
                    <UButton
                        icon="i-lucide-send"
                        :label="t('core.messages.send')"
                        :loading="sending"
                        :disabled="!newMessage.trim()"
                        @click="sendMessage"
                    />
                </div>
            </div>

            <div v-else class="closed-notice">
                <UIcon name="i-lucide-lock" />
                {{ t('core.messages.conversationClosedNotice') }}
            </div>
        </template>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.conversation-page-wrapper {
    @apply flex flex-col flex-1 min-h-0;
}

.conversation-top {
    @apply py-4 border-b border-gray-200 dark:border-gray-700;
}

.back-link {
    @apply flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 no-underline text-sm mb-3;
}

.loading-state,
.error-state {
    @apply flex flex-col items-center justify-center flex-1 gap-4;
}

.conversation-header {
    @apply flex items-start justify-between;
}

.header-info {
    @apply flex flex-col gap-1;
}

.conversation-subject {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100;
}

.conversation-date {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.header-badges {
    @apply flex gap-2;
}

.messages-container {
    @apply flex-1 min-h-0 overflow-y-auto;
    @apply bg-gray-50 dark:bg-slate-800/50;
}

.messages-inner {
    @apply py-4 space-y-4;
}

.message {
    @apply flex;
}

.message.own-message {
    @apply justify-end;
}

.message-bubble {
    @apply w-[80%] rounded-lg p-3;
    @apply bg-gray-100 dark:bg-gray-800;
}

.own-message .message-bubble {
    @apply bg-primary-100 dark:bg-primary-900/30;
}

.message-header {
    @apply flex items-center justify-between gap-4 mb-1;
}

.message-sender {
    @apply text-xs font-medium text-gray-700 dark:text-gray-300;
}

.message-time {
    @apply text-xs text-gray-500 dark:text-gray-400;
}

.message-content {
    @apply text-gray-900 dark:text-gray-100 whitespace-pre-wrap break-words;
}

.no-messages {
    @apply text-center text-gray-500 dark:text-gray-400 py-8;
}

.message-input-area {
    @apply py-4 border-t border-gray-200 dark:border-gray-700;
}

.input-inner {
    @apply flex gap-2;
}

.message-input {
    @apply flex-1;
}

.closed-notice {
    @apply flex items-center justify-center gap-2 py-4 text-gray-500 dark:text-gray-400;
    @apply border-t border-gray-200 dark:border-gray-700;
}
</style>
