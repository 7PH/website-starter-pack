<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import { requestAccountDeletion } from '~/utils/api/users';

const { t } = useI18n();
const { showSuccess, showErrorWithTitle } = useToastHelpers();

const isModalOpen = ref(false);
const isSending = ref(false);

async function sendDeletionEmail() {
    isSending.value = true;
    try {
        await requestAccountDeletion();
        isModalOpen.value = false;
        showSuccess(t('core.account.privacy.requestModal.sentTitle'), t('core.account.privacy.requestModal.sentBody'));
    } catch (error) {
        // Always direct the user to support so they have a path forward when
        // the in-app flow can't complete (email outage, rate limit, etc.).
        showErrorWithTitle(
            t('core.account.privacy.requestModal.failedTitle'),
            error,
            'core.account.privacy.requestModal.failedBody',
        );
    } finally {
        isSending.value = false;
    }
}
</script>

<template>
    <UCard>
        <template #header>
            <div>
                <h2 class="text-lg font-semibold">{{ t('core.account.privacy.deleteSection.title') }}</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                    {{ t('core.account.privacy.deleteSection.description') }}
                </p>
            </div>
        </template>

        <div class="flex justify-end">
            <UButton
                color="error"
                variant="solid"
                icon="i-lucide-trash-2"
                :label="t('core.account.privacy.deleteSection.button')"
                @click="isModalOpen = true"
            />
        </div>

        <UModal v-model:open="isModalOpen" :title="t('core.account.privacy.requestModal.title')">
            <template #body>
                <p>{{ t('core.account.privacy.requestModal.body') }}</p>
            </template>
            <template #footer>
                <div class="flex w-full justify-end gap-2">
                    <UButton
                        color="neutral"
                        variant="ghost"
                        :label="t('core.common.cancel')"
                        :disabled="isSending"
                        @click="isModalOpen = false"
                    />
                    <UButton
                        color="error"
                        :label="t('core.account.privacy.requestModal.confirm')"
                        :loading="isSending"
                        @click="sendDeletionEmail"
                    />
                </div>
            </template>
        </UModal>
    </UCard>
</template>
