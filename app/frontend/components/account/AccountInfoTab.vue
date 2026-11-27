<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import * as usersApi from '~/utils/api/users';

const auth = useAuth();
const accountActions = useAccountActions();
const { t } = useI18n();
const backendConfig = useBackendConfig();
const usernamesEnabled = computed(() => backendConfig.config?.usernames_enabled === true);
const realNamesEnabled = computed(() => backendConfig.config?.real_names_enabled !== false);
const { validateUsername } = useUsernameRules();

// Loading states
const isProfileLoading = ref(false);
const isEmailLoading = ref(false);

// Form errors
const profileErrors = ref<Record<string, string>>({});
const emailErrors = ref<Record<string, string>>({});

// Profile form
const profileForm = reactive({
    firstName: auth.user?.first_name || '',
    lastName: auth.user?.last_name || '',
    username: auth.user?.username || '',
    customData: (auth.user?.custom_data ?? {}) as UserCustomData,
});

// The token's copy goes stale once the user verifies from the email link, so read the live value.
onMounted(async () => {
    try {
        auth.updateUser(await usersApi.getCurrentUser());
    } catch {
        // Keep the token's copy
    }
});

const isResendingVerification = ref(false);
async function resendVerification() {
    isResendingVerification.value = true;
    await accountActions.sendVerificationEmail();
    isResendingVerification.value = false;
}

// Email form
const emailForm = reactive({
    newEmail: '',
    password: '',
});
const showEmailForm = ref(false);

// Watch for user changes to update profile form
watch(
    () => auth.user,
    (user) => {
        if (user) {
            profileForm.firstName = user.first_name ?? '';
            profileForm.lastName = user.last_name ?? '';
            profileForm.username = user.username ?? '';
            profileForm.customData = (user.custom_data ?? {}) as UserCustomData;
        }
    },
    { immediate: true },
);

// Validations
function validateProfile(): boolean {
    profileErrors.value = {};
    if (realNamesEnabled.value && !profileForm.firstName.trim()) {
        profileErrors.value.firstName = t('core.validation.required');
    }
    // Blank is only "leave it alone" for users who never got a handle (OAuth and
    // access-code signups). Once you have one you can rename it but not remove
    // it, so blanking the field is an error rather than a silent no-op.
    if (usernamesEnabled.value) {
        const blank = !profileForm.username.trim();
        if (blank && auth.user?.username) {
            profileErrors.value.username = t('core.validation.required');
        } else if (!blank) {
            const usernameError = validateUsername(profileForm.username);
            if (usernameError) profileErrors.value.username = usernameError;
        }
    }
    return Object.keys(profileErrors.value).length === 0;
}

function validateEmail(): boolean {
    emailErrors.value = {};
    if (!emailForm.newEmail.trim()) {
        emailErrors.value.newEmail = t('core.validation.required');
    }
    if (!emailForm.password) {
        emailErrors.value.password = t('core.validation.required');
    }
    return Object.keys(emailErrors.value).length === 0;
}

// Actions
async function handleProfileSave() {
    if (!validateProfile()) return;

    isProfileLoading.value = true;
    await accountActions.updateProfile(
        profileForm.firstName.trim(),
        profileForm.lastName.trim(),
        profileForm.customData,
        usernamesEnabled.value ? profileForm.username.trim() || undefined : undefined,
    );
    isProfileLoading.value = false;
}

async function handleEmailChange() {
    if (!validateEmail()) return;

    isEmailLoading.value = true;
    const success = await accountActions.requestEmailChange(emailForm.newEmail.trim(), emailForm.password);
    isEmailLoading.value = false;

    if (success) {
        emailForm.newEmail = '';
        emailForm.password = '';
        showEmailForm.value = false;
    }
}

function cancelEmailChange() {
    emailForm.newEmail = '';
    emailForm.password = '';
    emailErrors.value = {};
    showEmailForm.value = false;
}
</script>

<template>
    <div class="space-y-6">
        <!-- Profile Section -->
        <UCard>
            <template #header>
                <div>
                    <h2 class="text-lg font-semibold">{{ t('core.account.profile.title') }}</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        {{ t('core.account.profile.description') }}
                    </p>
                </div>
            </template>

            <form class="flex flex-col gap-4" @submit.prevent="handleProfileSave">
                <UFormField
                    v-if="usernamesEnabled"
                    :label="t('core.auth.username')"
                    :error="profileErrors.username"
                    :help="t('core.auth.usernameHelp')"
                >
                    <UInput
                        v-model="profileForm.username"
                        autocomplete="username"
                        :color="profileErrors.username ? 'error' : undefined"
                        class="w-full"
                    />
                </UFormField>

                <div v-if="realNamesEnabled" class="flex gap-4">
                    <UFormField :label="t('core.auth.firstName')" :error="profileErrors.firstName" class="flex-1">
                        <UInput
                            v-model="profileForm.firstName"
                            autocomplete="given-name"
                            :color="profileErrors.firstName ? 'error' : undefined"
                            class="w-full"
                        />
                    </UFormField>

                    <UFormField :label="t('core.auth.lastName')" :error="profileErrors.lastName" class="flex-1">
                        <UInput
                            v-model="profileForm.lastName"
                            autocomplete="family-name"
                            :color="profileErrors.lastName ? 'error' : undefined"
                            class="w-full"
                        />
                    </UFormField>
                </div>

                <UsersMetadataFields
                    :custom-data="profileForm.customData"
                    @update:custom-data="profileForm.customData = $event"
                />

                <div class="flex justify-end">
                    <UButton type="submit" :label="t('core.account.save')" :loading="isProfileLoading" />
                </div>
            </form>
        </UCard>

        <!-- Email Section -->
        <UCard>
            <template #header>
                <div>
                    <h2 class="text-lg font-semibold">{{ t('core.account.email.title') }}</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        {{ t('core.account.email.description') }}
                    </p>
                </div>
            </template>

            <div class="flex flex-col gap-4">
                <!-- Current email display -->
                <div v-if="!showEmailForm">
                    <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                        {{ t('core.account.email.current') }}
                    </p>
                    <p class="font-medium flex items-center gap-2">
                        {{ auth.user?.email }}
                        <UBadge
                            v-if="auth.user?.email_confirmed != null"
                            :color="auth.user.email_confirmed ? 'success' : 'warning'"
                            variant="subtle"
                            size="sm"
                            :label="
                                auth.user.email_confirmed
                                    ? t('core.account.email.verified')
                                    : t('core.account.email.notVerified')
                            "
                        />
                    </p>
                    <UButton
                        v-if="auth.user?.email_confirmed === false && backendConfig.config?.email_enabled !== false"
                        class="mt-4 mr-2"
                        variant="soft"
                        :label="t('core.account.email.sendVerification')"
                        :loading="isResendingVerification"
                        @click="resendVerification"
                    />
                    <UButton
                        class="mt-4"
                        variant="outline"
                        :label="t('core.account.email.change')"
                        @click="showEmailForm = true"
                    />
                </div>

                <!-- Email change form -->
                <form v-else class="flex flex-col gap-4" @submit.prevent="handleEmailChange">
                    <UFormField :label="t('core.account.email.newEmail')" :error="emailErrors.newEmail">
                        <UInput
                            v-model="emailForm.newEmail"
                            type="email"
                            autocomplete="email"
                            :color="emailErrors.newEmail ? 'error' : undefined"
                            class="w-full"
                        />
                    </UFormField>

                    <UFormField :label="t('core.account.email.confirmWithPassword')" :error="emailErrors.password">
                        <UiPasswordInput
                            v-model="emailForm.password"
                            autocomplete="current-password"
                            :error="!!emailErrors.password"
                        />
                    </UFormField>

                    <div class="flex gap-2 justify-end">
                        <UButton
                            variant="ghost"
                            color="neutral"
                            :label="t('core.account.cancel')"
                            @click="cancelEmailChange"
                        />
                        <UButton
                            type="submit"
                            :label="t('core.account.email.sendVerification')"
                            :loading="isEmailLoading"
                        />
                    </div>
                </form>
            </div>
        </UCard>
    </div>
</template>
