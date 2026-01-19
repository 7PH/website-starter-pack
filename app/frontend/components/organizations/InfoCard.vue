<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatDate } from '~/utils/formatters';

const props = defineProps<{
    org: OrganizationRead;
    isAdminView: boolean;
    isEditing: boolean;
    isSaving: boolean;
}>();

// Use defineModel for two-way binding of form fields
const formName = defineModel<string>('formName', { required: true });
const formEmail = defineModel<string>('formEmail', { required: true });
const formDescription = defineModel<string | null>('formDescription');
const formPhone = defineModel<string | null>('formPhone');
const formTaxNumber = defineModel<string | null>('formTaxNumber');
const formAddressLine1 = defineModel<string | null>('formAddressLine1');
const formAddressLine2 = defineModel<string | null>('formAddressLine2');
const formCity = defineModel<string | null>('formCity');
const formState = defineModel<string | null>('formState');
const formPostalCode = defineModel<string | null>('formPostalCode');
const formCountry = defineModel<string | null>('formCountry');
const formCustomData = defineModel<OrganizationCustomData>('formCustomData', { required: true });

const emit = defineEmits<{
    startEdit: [];
    cancelEdit: [];
    save: [];
}>();

const { t } = useI18n();
</script>

<template>
    <UCard class="info-card">
        <template #header>
            <UiCardHeader :title="t('core.organizations.details')">
                <template #actions>
                    <UButton
                        v-if="!isEditing && !org.deleted_at"
                        :label="t('core.organizations.edit')"
                        icon="i-lucide-pencil"
                        size="sm"
                        color="neutral"
                        variant="outline"
                        @click="emit('startEdit')"
                    />
                </template>
            </UiCardHeader>
        </template>

        <form v-if="isEditing" class="edit-form" @submit.prevent="emit('save')">
            <div class="form-row">
                <UFormField :label="t('core.organizations.name')" class="flex-1">
                    <UInput v-model="formName" />
                </UFormField>
                <UFormField :label="t('core.organizations.email')" class="flex-1">
                    <UInput v-model="formEmail" type="email" />
                </UFormField>
            </div>
            <UFormField :label="t('core.organizations.descriptionLabel')">
                <UTextarea v-model="formDescription" :rows="2" />
            </UFormField>
            <div class="form-row">
                <UFormField :label="t('core.organizations.phone')" class="flex-1">
                    <UInput v-model="formPhone" />
                </UFormField>
                <UFormField :label="t('core.organizations.taxNumber')" class="flex-1">
                    <UInput v-model="formTaxNumber" />
                </UFormField>
            </div>
            <UFormField :label="t('core.organizations.addressLine1')">
                <UInput v-model="formAddressLine1" />
            </UFormField>
            <UFormField :label="t('core.organizations.addressLine2')">
                <UInput v-model="formAddressLine2" />
            </UFormField>
            <div class="form-row">
                <UFormField :label="t('core.organizations.city')" class="flex-1">
                    <UInput v-model="formCity" />
                </UFormField>
                <UFormField :label="t('core.organizations.state')" class="flex-1">
                    <UInput v-model="formState" />
                </UFormField>
            </div>
            <div class="form-row">
                <UFormField :label="t('core.organizations.postalCode')" class="flex-1">
                    <UInput v-model="formPostalCode" />
                </UFormField>
                <UFormField :label="t('core.organizations.country')" class="flex-1">
                    <UInput
                        v-model="formCountry"
                        :placeholder="t('core.organizations.countryPlaceholder')"
                        maxlength="2"
                    />
                </UFormField>
            </div>
            <OrganizationsMetadataFields :custom-data="formCustomData" @update:custom-data="formCustomData = $event" />
            <UiFormActions>
                <UButton
                    :label="t('core.organizations.cancel')"
                    color="neutral"
                    variant="outline"
                    @click="emit('cancelEdit')"
                />
                <UButton type="submit" :label="t('core.organizations.save')" :loading="isSaving" />
            </UiFormActions>
        </form>

        <div v-else class="info-grid">
            <div v-if="isAdminView" class="info-item">
                <span class="info-label">{{ t('core.organizations.id') }}</span>
                <span class="info-value">#{{ org.id }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">{{ t('core.organizations.email') }}</span>
                <span class="info-value">{{ org.email }}</span>
            </div>
            <div v-if="org.description" class="info-item">
                <span class="info-label">{{ t('core.organizations.descriptionLabel') }}</span>
                <span class="info-value">{{ org.description }}</span>
            </div>
            <div v-if="org.phone" class="info-item">
                <span class="info-label">{{ t('core.organizations.phone') }}</span>
                <span class="info-value">{{ org.phone }}</span>
            </div>
            <div v-if="org.tax_number" class="info-item">
                <span class="info-label">{{ t('core.organizations.taxNumber') }}</span>
                <span class="info-value">{{ org.tax_number }}</span>
            </div>
            <div v-if="org.address_line1 || org.city" class="info-item">
                <span class="info-label">{{ t('core.organizations.addressLine1') }}</span>
                <span class="info-value">
                    {{
                        [org.address_line1, org.address_line2, org.city, org.state, org.postal_code, org.country]
                            .filter(Boolean)
                            .join(', ')
                    }}
                </span>
            </div>
            <div v-if="isAdminView" class="info-item">
                <span class="info-label">{{ t('core.organizations.created') }}</span>
                <span class="info-value">{{ formatDate(org.created_at) }}</span>
            </div>
            <div v-if="isAdminView && org.stripe_premium" class="info-item">
                <span class="info-label">{{ t('core.organizations.premiumQuota') }}</span>
                <span class="info-value">
                    {{ t('core.organizations.seatsUsed', { used: org.premium_member_count, total: org.stripe_quota }) }}
                </span>
            </div>
            <div v-if="isAdminView && org.deleted_at" class="info-item">
                <span class="info-label">{{ t('core.organizations.deleted') }}</span>
                <span class="info-value deleted-value">{{ formatDate(org.deleted_at) }}</span>
            </div>
            <OrganizationsMetadataDisplay :custom-data="(org.custom_data as OrganizationCustomData) ?? {}" />
        </div>
    </UCard>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.info-grid {
    @apply grid gap-4;
}

.info-item {
    @apply flex flex-col gap-1;
}

.info-label {
    @apply text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide;
}

.info-value {
    @apply text-sm text-gray-900 dark:text-gray-100;
}

.info-value.deleted-value {
    @apply text-red-600 dark:text-red-400;
}

.edit-form {
    @apply flex flex-col gap-4;
}

.form-row {
    @apply grid grid-cols-1 sm:grid-cols-2 gap-4;
}
</style>
