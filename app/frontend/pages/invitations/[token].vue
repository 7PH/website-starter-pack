<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import { acceptInvitation, declineInvitation, previewInvitation } from '~/utils/api/invitations';

definePageMeta({
    // Page is reachable logged-out; the preview endpoint is public.
});

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const { t } = useI18n();
const { showSuccess, showError } = useToastHelpers();

const token = computed(() => String(route.params.token));

const preview = ref<PendingInvitationPreview | null>(null);
const pending = ref(true);
const loadError = ref<string | null>(null);
const busy = ref(false);

async function load() {
    pending.value = true;
    try {
        preview.value = await previewInvitation(token.value);
    } catch (error: unknown) {
        const msg = error instanceof Error ? error.message : String(error);
        if (msg.includes('410') || msg.includes('expired')) {
            loadError.value = t('core.organizations.invitationExpired');
        } else {
            loadError.value = t('core.organizations.invitationInvalid');
        }
    } finally {
        pending.value = false;
    }
}

const emailMismatch = computed(() => {
    if (!preview.value || !auth.user) return false;
    return preview.value.email.toLowerCase() !== auth.user.email.toLowerCase();
});

async function accept() {
    if (!auth.isLoggedIn) {
        router.push({ path: '/login', query: { redirect: route.fullPath, email: preview.value?.email } });
        return;
    }
    busy.value = true;
    try {
        await acceptInvitation(token.value);
        showSuccess(t('core.organizations.invitationAccepted'));
        await auth.refreshToken();
        router.push('/account?tab=organizations');
    } catch (error: unknown) {
        showError(error, 'core.errors.generic');
    } finally {
        busy.value = false;
    }
}

async function decline() {
    if (!auth.isLoggedIn) {
        router.push({ path: '/login', query: { redirect: route.fullPath, email: preview.value?.email } });
        return;
    }
    busy.value = true;
    try {
        await declineInvitation(token.value);
        showSuccess(t('core.organizations.invitationDeclined'));
        router.push('/account?tab=organizations');
    } catch (error: unknown) {
        showError(error, 'core.errors.generic');
    } finally {
        busy.value = false;
    }
}

onMounted(load);
</script>

<template>
    <div class="page-box invitation-page">
        <UCard>
            <div v-if="pending" class="loading">
                <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary-500" />
            </div>

            <UAlert
                v-else-if="loadError"
                color="error"
                variant="subtle"
                icon="i-lucide-alert-triangle"
                :title="loadError"
            />

            <div v-else-if="preview" class="content">
                <UIcon name="i-lucide-building-2" class="text-4xl text-primary-500" />
                <h1 class="title">
                    {{ t('core.organizations.invitationFrom', { orgName: preview.organization_name }) }}
                </h1>
                <p v-if="preview.invited_by_name" class="hint">
                    {{ preview.invited_by_name }}
                </p>
                <p class="hint">
                    {{
                        t('core.organizations.invitedAs', {
                            role: preview.is_admin_invite
                                ? t('core.organizations.admin')
                                : t('core.organizations.member'),
                        })
                    }}
                </p>

                <UAlert
                    v-if="!auth.isLoggedIn"
                    color="info"
                    variant="subtle"
                    icon="i-lucide-info"
                    :description="t('core.organizations.invitationLoginPrompt')"
                    class="mt-4"
                />

                <UAlert
                    v-if="auth.isLoggedIn && emailMismatch"
                    color="warning"
                    variant="subtle"
                    icon="i-lucide-alert-triangle"
                    :description="t('core.organizations.invitationInvalid')"
                    class="mt-4"
                />

                <div class="actions">
                    <UButton
                        :label="t('core.organizations.invitationAccept')"
                        icon="i-lucide-check"
                        color="primary"
                        :loading="busy"
                        :disabled="auth.isLoggedIn && emailMismatch"
                        @click="accept"
                    />
                    <UButton
                        :label="t('core.organizations.invitationDecline')"
                        icon="i-lucide-x"
                        color="neutral"
                        variant="outline"
                        :loading="busy"
                        :disabled="auth.isLoggedIn && emailMismatch"
                        @click="decline"
                    />
                </div>
            </div>
        </UCard>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.invitation-page {
    @apply max-w-xl mx-auto py-12;
}

.loading {
    @apply flex justify-center py-12;
}

.content {
    @apply flex flex-col items-center text-center gap-2 py-6;
}

.title {
    @apply text-xl font-semibold text-gray-900 dark:text-gray-100 m-0;
}

.hint {
    @apply text-sm text-gray-600 dark:text-gray-400 m-0;
}

.actions {
    @apply mt-6 flex gap-3;
}
</style>
