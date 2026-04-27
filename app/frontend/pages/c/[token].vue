<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    layout: 'auth',
    middleware: ['managed-accounts-enabled'],
});

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const { showError } = useToastHelpers();
const api = useApi();
const accessCode = useAccessCode();
const pickerLink = usePickerLink();

const token = computed(() => String(route.params.token));

const payload = ref<PublicPickerPayload | null>(null);
const isLoading = ref(true);
const notFound = ref(false);

const selectedId = ref<number | null>(null);
const code = ref('');
const isSigningIn = ref(false);

async function load() {
    isLoading.value = true;
    notFound.value = false;
    try {
        payload.value = await api.get<PublicPickerPayload>(`/c/${token.value}`);
        // Pre-select the last name this browser used, if any.
        const remembered = pickerLink.read();
        if (remembered?.token === token.value && remembered.lastAccountId) {
            selectedId.value = remembered.lastAccountId;
        }
    } catch {
        notFound.value = true;
    } finally {
        isLoading.value = false;
    }
}

onMounted(load);

watchEffect(() => {
    if (payload.value && token.value) {
        pickerLink.write({
            token: token.value,
            lastAccountId: selectedId.value,
            groupName: payload.value.group_name,
        });
    }
});

const selected = computed(() => payload.value?.members.find((m) => m.managed_account_id === selectedId.value) ?? null);

async function signIn() {
    if (!selectedId.value || !code.value.trim()) return;
    isSigningIn.value = true;
    try {
        await accessCode.signInWithCode({
            managedAccountId: selectedId.value,
            code: code.value.trim(),
        });
        await router.push('/');
    } catch (error) {
        showError(error, 'core.managed_accounts.signInFailed');
    } finally {
        isSigningIn.value = false;
    }
}

function back() {
    selectedId.value = null;
    code.value = '';
}
</script>

<template>
    <div class="picker">
        <div v-if="isLoading" class="picker__state">
            <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin" />
        </div>

        <EmptyState
            v-else-if="notFound"
            :title="t('core.managed_accounts.linkNotFoundTitle')"
            :description="t('core.managed_accounts.linkNotFoundDescription')"
            icon="i-lucide-link-2-off"
        />

        <template v-else-if="payload">
            <header class="picker__header">
                <h1 class="picker__title">{{ payload.group_name }}</h1>
                <p v-if="!selected" class="picker__subtitle">
                    {{ t('core.managed_accounts.findYourName') }}
                </p>
                <p v-else class="picker__subtitle">
                    {{ t('core.managed_accounts.enterYourCode') }}
                </p>
            </header>

            <div v-if="!selected">
                <EmptyState
                    v-if="!payload.members.length"
                    :title="t('core.managed_accounts.noNamesYet')"
                    :description="t('core.managed_accounts.noNamesYetDescription')"
                    icon="i-lucide-users"
                />
                <div v-else class="picker__grid">
                    <button
                        v-for="member in payload.members"
                        :key="member.managed_account_id"
                        type="button"
                        class="picker__name"
                        @click="selectedId = member.managed_account_id"
                    >
                        {{
                            member.display_name || t('core.user.display.fallback_id', { id: member.managed_account_id })
                        }}
                    </button>
                </div>
            </div>

            <form v-else class="picker__form" @submit.prevent="signIn">
                <div class="picker__selected">
                    <p class="picker__selected-name">
                        {{
                            selected.display_name ||
                            t('core.user.display.fallback_id', { id: selected.managed_account_id })
                        }}
                    </p>
                    <UButton color="neutral" variant="ghost" size="sm" @click="back">
                        {{ t('core.managed_accounts.notMe') }}
                    </UButton>
                </div>
                <UFormField :label="t('core.managed_accounts.code')" class="w-full">
                    <UInput
                        v-model="code"
                        autofocus
                        autocomplete="off"
                        :placeholder="t('core.managed_accounts.codePlaceholder')"
                        size="lg"
                        class="w-full"
                        :ui="{ base: 'font-mono tracking-widest text-center' }"
                    />
                </UFormField>
                <UButton type="submit" color="primary" block size="lg" :loading="isSigningIn" :disabled="!code.trim()">
                    {{ t('core.managed_accounts.signIn') }}
                </UButton>
            </form>
        </template>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.picker {
    @apply mx-auto max-w-xl py-10 px-4 space-y-6;
}

.picker__state {
    @apply text-center py-10;
}

.picker__header {
    @apply text-center space-y-1;
}

.picker__title {
    @apply text-2xl font-semibold text-gray-900 dark:text-gray-100;
}

.picker__subtitle {
    @apply text-gray-500 dark:text-gray-400;
}

.picker__grid {
    @apply grid grid-cols-1 sm:grid-cols-2 gap-2;
}

.picker__name {
    @apply px-4 py-4 rounded-lg
           border border-gray-200 dark:border-gray-700
           bg-white dark:bg-gray-800
           text-base font-medium text-gray-900 dark:text-gray-100
           hover:border-primary-400 hover:bg-primary-50
           dark:hover:bg-primary-950
           transition-colors;
}

.picker__form {
    @apply space-y-4;
}

.picker__selected {
    @apply flex items-center justify-between gap-3 p-4 rounded-lg
           bg-primary-50 dark:bg-primary-950/30
           border border-primary-200 dark:border-primary-900;
}

.picker__selected-name {
    @apply text-lg font-medium text-gray-900 dark:text-gray-100;
}
</style>
