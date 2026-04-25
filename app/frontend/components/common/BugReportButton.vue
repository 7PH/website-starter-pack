<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
/**
 * Navbar-friendly trigger that opens a bug-report (or feature-request) modal.
 * Self-contained: it manages its own auth gate and modal state.
 * Submission goes through the shared ConversationComposerModal.
 */
withDefaults(
    defineProps<{
        /** Server-side subtype. Defaults to 'bug_report'. Apps can pass 'feature_request' or any user-initiable subtype. */
        subtype?: ConversationCreate['subtype'];
        /** Tooltip override. Defaults to the i18n key. */
        label?: string;
    }>(),
    {
        subtype: 'bug_report',
        label: undefined,
    },
);

const { t } = useI18n();
const auth = useAuth();

const open = ref(false);
</script>

<template>
    <template v-if="auth.isLoggedIn">
        <UButton
            icon="i-lucide-bug"
            color="neutral"
            variant="ghost"
            :aria-label="label ?? t('core.bug_report.trigger_label')"
            @click="open = true"
        />
        <MessagesConversationComposerModal
            v-model:open="open"
            :subtype="subtype"
            :show-subject="false"
            :subject-prefix="t('core.bug_report.modal.subject_prefix')"
            :show-captured-context="true"
            :title="t('core.bug_report.modal.title')"
            :placeholder="t('core.bug_report.modal.placeholder')"
        />
    </template>
</template>
