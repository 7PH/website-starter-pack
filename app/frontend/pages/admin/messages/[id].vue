<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import * as conversationsApi from '~/utils/api/conversations';
import { formatDate, formatTime, previewLabel } from '~/utils/formatters';

definePageMeta({
    middleware: ['admin'],
});

const route = useRoute();
const { showSuccess, showError } = useToastHelpers();
const modal = useModalStore();

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
        loadAdminNavBadges();
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
</script>

<template>
    <div class="flex min-h-0 flex-1 flex-col gap-4.5">
        <NuxtLink
            to="/admin/messages"
            class="flex items-center gap-1.5 self-start text-[13px] font-bold text-muted hover:text-highlighted"
        >
            <UIcon name="i-lucide-arrow-left" />
            All messages
        </NuxtLink>

        <LoadingSkeleton v-if="pending" class="h-96" />

        <UAlert
            v-else-if="!conversation"
            color="error"
            variant="subtle"
            icon="i-lucide-message-square-x"
            title="Conversation not found"
        />

        <template v-else>
            <AdminPageHeader :title="conversation.subject || '(No subject)'">
                <template #badges>
                    <UBadge
                        :label="conversation.is_closed ? 'Closed' : 'Open'"
                        :color="conversation.is_closed ? 'neutral' : 'success'"
                        variant="soft"
                        class="rounded-full"
                    />
                </template>
                <template #description>
                    From <strong class="text-highlighted">{{ previewLabel(conversation.created_by) }}</strong>
                    <template v-if="conversation.created_by">
                        (<NuxtLink
                            :to="`/admin/users/${conversation.created_by.id}`"
                            class="text-primary hover:underline"
                            >{{ conversation.created_by.email }}</NuxtLink
                        >)
                    </template>
                    · {{ formatDate(conversation.created_at) }}
                </template>
                <template #actions>
                    <UButton
                        v-if="conversation.is_closed"
                        icon="i-lucide-lock-open"
                        label="Reopen"
                        size="lg"
                        color="neutral"
                        variant="outline"
                        :loading="actionPending"
                        @click="reopenConversation"
                    />
                    <UButton
                        v-else
                        icon="i-lucide-lock"
                        label="Close"
                        size="lg"
                        color="neutral"
                        variant="outline"
                        :loading="actionPending"
                        @click="closeConversation"
                    />
                </template>
            </AdminPageHeader>

            <!-- Not an AdminCard: the thread has to fill the remaining height and scroll on its own -->
            <section class="flex min-h-80 flex-1 flex-col overflow-hidden rounded-xl border border-default bg-default">
                <div ref="messagesContainer" class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4.5">
                    <div
                        v-for="message in conversation.messages"
                        :key="message.id"
                        class="flex"
                        :class="message.is_admin_response ? 'justify-end' : 'justify-start'"
                    >
                        <div
                            class="max-w-[85%] rounded-xl px-3.5 py-2.5 md:max-w-[75%]"
                            :class="message.is_admin_response ? 'bg-primary-100 dark:bg-primary-500/15' : 'bg-elevated'"
                        >
                            <div class="mb-1 flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                                <span class="flex items-center gap-1.5 text-xs font-bold text-toned">
                                    {{ previewLabel(message.sender) }}
                                    <UBadge
                                        v-if="message.is_admin_response"
                                        label="Admin"
                                        color="info"
                                        variant="soft"
                                        size="sm"
                                        class="rounded-full"
                                    />
                                </span>
                                <span class="text-xs text-dimmed">
                                    {{ formatDate(message.created_at) }} {{ formatTime(message.created_at) }}
                                </span>
                            </div>
                            <MessageContent :content="message.content" />
                        </div>
                    </div>

                    <p v-if="!conversation.messages?.length" class="py-8 text-center text-sm text-muted">
                        No messages yet
                    </p>
                </div>

                <div v-if="!conversation.is_closed" class="flex flex-col gap-3 border-t border-default p-4.5">
                    <div class="flex gap-1">
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
                        class="w-full"
                        @keydown.ctrl.enter="sendMessage"
                        @keydown.meta.enter="sendMessage"
                    />
                    <div
                        v-show="composeMode === 'preview'"
                        class="min-h-20 w-full rounded-md border border-default bg-elevated p-3"
                    >
                        <MessageContent :content="newMessage" />
                    </div>
                    <UButton
                        icon="i-lucide-send"
                        label="Send reply"
                        size="lg"
                        class="self-end"
                        :loading="sending"
                        :disabled="!newMessage.trim()"
                        @click="sendMessage"
                    />
                </div>

                <div
                    v-else
                    class="flex items-center justify-center gap-2 border-t border-default p-4 text-sm text-muted"
                >
                    <UIcon name="i-lucide-lock" />
                    This conversation is closed. Reopen it to send messages.
                </div>
            </section>
        </template>
    </div>
</template>
