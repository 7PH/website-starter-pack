<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import * as conversationsApi from '~/utils/api/conversations';
import { buildAutoSubject, buildBugReportBody, captureContext, type CapturedContext } from '~/utils/bug-report';

const props = withDefaults(
    defineProps<{
        /** v-model:open — matches UModal convention */
        open: boolean;
        /** Server-side subtype (omitted for generic conversations). Typed to whatever the backend currently accepts. */
        subtype?: ConversationCreate['subtype'];
        /** Show the subject input. When false, subject is auto-generated from the content. */
        showSubject?: boolean;
        /** Prefix prepended to the auto-generated subject (used when showSubject=false) */
        subjectPrefix?: string;
        /** Append an auto-captured URL/UA/viewport block to the submitted body */
        showCapturedContext?: boolean;
        /** Content length cap (server enforces too) */
        maxLength?: number;
        /** Modal title */
        title?: string;
        /** Textarea placeholder */
        placeholder?: string;
    }>(),
    {
        subtype: undefined,
        showSubject: true,
        subjectPrefix: '',
        showCapturedContext: false,
        maxLength: 10000,
        title: undefined,
        placeholder: undefined,
    },
);

const emit = defineEmits<{
    'update:open': [value: boolean];
}>();

const { t } = useI18n();
const { showError } = useToastHelpers();
const router = useRouter();

const isOpen = computed({
    get: () => props.open,
    set: (v: boolean) => emit('update:open', v),
});

const form = ref({ subject: '', content: '' });
const submitting = ref(false);

// Captured context is read when the modal opens (not every render) so values stay stable.
const captured = ref<CapturedContext>({ url: '', userAgent: '', viewport: '' });

watch(isOpen, (open) => {
    if (!open) return;
    form.value = { subject: '', content: '' };
    if (import.meta.client && props.showCapturedContext) {
        captured.value = captureContext({
            locationHref: window.location.href,
            userAgent: navigator.userAgent,
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
        });
    }
});

const modalTitle = computed(() => props.title ?? t('core.messages.newConversation'));
const modalPlaceholder = computed(() => props.placeholder ?? t('core.messages.messagePlaceholder'));
const charCount = computed(() => form.value.content.length);
const tooLong = computed(() => charCount.value > props.maxLength);
const canSubmit = computed(() => !submitting.value && form.value.content.trim().length > 0 && !tooLong.value);

function buildBody(): string {
    const description = form.value.content.trim();
    if (!props.showCapturedContext) return description;
    return buildBugReportBody(description, captured.value);
}

function buildSubject(): string {
    if (props.showSubject) return form.value.subject.trim();
    return buildAutoSubject(form.value.content, props.subjectPrefix);
}

async function submit() {
    if (!canSubmit.value) {
        showError(new Error(t('core.messages.messageRequired')), 'core.messages.messageRequired');
        return;
    }

    submitting.value = true;
    try {
        const conversation = await conversationsApi.createConversation({
            subject: buildSubject() || t('core.messages.noSubject'),
            content: buildBody(),
            subtype: props.subtype,
        });
        isOpen.value = false;
        router.push(`/messages/${conversation.id}`);
    } catch (error) {
        showError(error, 'core.messages.createFailed');
    } finally {
        submitting.value = false;
    }
}
</script>

<template>
    <UModal v-model:open="isOpen">
        <template #content>
            <UCard>
                <template #header>
                    <UiModalHeader :title="modalTitle" @close="isOpen = false" />
                </template>

                <div class="composer-form">
                    <UFormField v-if="showSubject" :label="t('core.messages.subjectLabel')">
                        <UInput
                            v-model="form.subject"
                            :placeholder="t('core.messages.subjectPlaceholder')"
                            class="w-full"
                        />
                    </UFormField>

                    <UFormField :label="t('core.messages.messageLabel')" required>
                        <UTextarea
                            v-model="form.content"
                            :placeholder="modalPlaceholder"
                            :rows="5"
                            :maxlength="maxLength"
                            class="w-full"
                        />
                        <template #help>
                            <span :class="tooLong ? 'text-red-500' : 'text-gray-500'">
                                {{ charCount }} / {{ maxLength }}
                            </span>
                        </template>
                    </UFormField>

                    <div v-if="showCapturedContext" class="captured-context">
                        <div class="captured-title">{{ t('core.bug_report.modal.context_label') }}</div>
                        <dl class="captured-grid">
                            <dt>{{ t('core.bug_report.modal.url_label') }}</dt>
                            <dd class="truncate">{{ captured.url }}</dd>
                            <dt>{{ t('core.bug_report.modal.useragent_label') }}</dt>
                            <dd class="truncate">{{ captured.userAgent }}</dd>
                            <dt>{{ t('core.bug_report.modal.viewport_label') }}</dt>
                            <dd>{{ captured.viewport }}</dd>
                        </dl>
                    </div>
                </div>

                <template #footer>
                    <UiFormActions>
                        <UButton
                            color="neutral"
                            variant="outline"
                            :label="t('core.common.cancel')"
                            @click="isOpen = false"
                        />
                        <UButton
                            :label="t('core.messages.send')"
                            :loading="submitting"
                            :disabled="!canSubmit"
                            @click="submit"
                        />
                    </UiFormActions>
                </template>
            </UCard>
        </template>
    </UModal>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.composer-form {
    @apply flex flex-col gap-4;
}
.captured-context {
    @apply rounded-md border border-gray-200 dark:border-gray-800 p-3 text-sm;
}
.captured-title {
    @apply font-medium text-gray-700 dark:text-gray-300 mb-2;
}
.captured-grid {
    @apply grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 text-gray-500 dark:text-gray-400;
}
.captured-grid dt {
    @apply font-medium text-gray-600 dark:text-gray-300;
}
.captured-grid dd {
    @apply min-w-0 break-all;
}
.truncate {
    @apply whitespace-nowrap overflow-hidden text-ellipsis;
}
</style>
