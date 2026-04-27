<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
const auth = useAuth();
const api = useApi();
const toast = useToast();
const { t } = useI18n();
const userDisplay = useUserDisplay();

const isLoading = ref(false);

const isAnyHandover = computed(() => auth.isImpersonating || auth.isOpenAsManagedAccount);

async function stopImpersonation() {
    isLoading.value = true;
    try {
        const response = await api.delete<ImpersonationResponse>('/admin/impersonations');

        // Update the auth store with the new token
        auth.saveUserToken({
            access_token: response.access_token,
            token_parsed: response.token_parsed,
            user: response.user,
            token_type: 'bearer',
        });

        toast.add({
            title: t('core.admin.impersonation.ended'),
            description: t('core.admin.impersonation.backToAdmin'),
            color: 'success',
            duration: 3000,
        });

        await navigateTo('/admin/users');
    } catch (error) {
        toast.add({
            title: t('core.errors.generic'),
            description: t('core.admin.impersonation.errorStopping'),
            color: 'error',
            duration: 3000,
        });
    } finally {
        isLoading.value = false;
    }
}

async function stopOpenAs() {
    isLoading.value = true;
    try {
        auth.stopOpenAs();
        toast.add({
            title: t('core.managed_accounts.openAsEnded'),
            color: 'success',
            duration: 3000,
        });
        await navigateTo('/managed-account-groups');
    } finally {
        isLoading.value = false;
    }
}
</script>

<template>
    <div v-if="isAnyHandover" class="impersonation-banner">
        <div class="flex items-center justify-center gap-3 max-w-7xl mx-auto">
            <UIcon name="i-lucide-user" class="text-xl" />
            <span v-if="auth.isImpersonating" class="text-sm">
                {{ t('core.admin.impersonation.viewingAs') }} <strong>{{ userDisplay.label(auth.user) }}</strong>
            </span>
            <span v-else class="text-sm">
                {{ t('core.managed_accounts.viewingAs') }} <strong>{{ userDisplay.label(auth.user) }}</strong>
            </span>
            <UButton
                :label="
                    auth.isImpersonating
                        ? t('core.admin.impersonation.exit')
                        : t('core.managed_accounts.backToMyAccount')
                "
                icon="i-lucide-log-out"
                size="sm"
                color="neutral"
                variant="solid"
                :loading="isLoading"
                @click="auth.isImpersonating ? stopImpersonation() : stopOpenAs()"
            />
        </div>
    </div>
</template>

<style scoped>
.impersonation-banner {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 0.5rem 1rem;
    position: sticky;
    top: 0;
    z-index: 50;
}
</style>
