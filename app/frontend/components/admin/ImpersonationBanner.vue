<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
const auth = useAuth();
const api = useApi();
const toast = useToast();
const { t } = useI18n();

const isLoading = ref(false);

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

        // Navigate back to admin
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
</script>

<template>
    <div v-if="auth.isImpersonating" class="impersonation-banner">
        <div class="banner-content">
            <UIcon name="i-lucide-user" class="banner-icon" />
            <span class="banner-text">
                {{ t('core.admin.impersonation.viewingAs') }} <strong>{{ auth.user?.email }}</strong>
            </span>
            <UButton
                :label="t('core.admin.impersonation.exit')"
                icon="i-lucide-log-out"
                size="sm"
                color="neutral"
                variant="solid"
                :loading="isLoading"
                @click="stopImpersonation"
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

.banner-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    max-width: 80rem;
    margin: 0 auto;
}

.banner-icon {
    font-size: 1.25rem;
}

.banner-text {
    font-size: 0.875rem;
}
</style>
