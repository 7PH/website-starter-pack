<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatDate } from '~/utils/formatters';
import { useOrganizationMembers, useOrganizationQuota } from '~/composables/organizations/useOrganizationMembers';
import { useOrganizationSubscription } from '~/composables/organizations/useOrganizationSubscription';
import { useOrganizationForm } from '~/composables/organizations/useOrganizationForm';
import { adminCreateConversation } from '~/utils/api/conversations';

export interface OrganizationDetailProps {
    /** Whether this is admin view (shows extra controls and links) */
    isAdminView?: boolean;
    /** Back link destination */
    backLink: string;
    /** Back link text */
    backLinkText: string;
}

const props = withDefaults(defineProps<OrganizationDetailProps>(), {
    isAdminView: false,
});

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const api = useApi();
const toast = useToast();
const modal = useModalStore();
const { t } = useI18n();
const { showSuccess, showError } = useToastHelpers();

const orgId = computed(() => Number(route.params.id));

// Check if auth is ready (user data loaded) - only needed for user view
const isAuthReady = computed(() => props.isAdminView || (auth.isLoggedIn && auth.user !== null));

// Check if user is an admin of this org (for user view access control)
const isUserOrgAdmin = computed(() => {
    if (props.isAdminView) return true; // Admin view bypasses this check
    const user = auth.user as UserRead | null;
    if (!user?.organizations) return false;
    const membership = user.organizations.find((o: UserOrganizationInfo) => o.organization_id === orgId.value);
    return membership?.is_admin === true;
});

// Fetch organization data
const {
    data: org,
    pending: orgPending,
    error: orgError,
    refresh: refreshOrg,
} = await useAsyncData<OrganizationRead>(
    `org-detail-${props.isAdminView ? 'admin' : 'user'}-${orgId.value}`,
    () => api.get(`/organizations/${orgId.value}`),
    { server: false },
);

// Organization form state (using shared composable)
const { form, isEditing, isSaving, cancelEdit } = useOrganizationForm(org);

// Member management callbacks (only for user view)
const memberCallbacks = props.isAdminView
    ? undefined
    : {
          onSelfDemoted: async () => {
              await auth.refreshToken();
              router.push('/account?tab=organizations');
          },
          onAuthRefreshNeeded: () => auth.refreshToken(),
      };

// Member management (using shared composable)
const {
    showAddMemberModal,
    addMemberEmail,
    addMemberAsAdmin,
    isAddingMember,
    addMember,
    toggleMemberAdmin: _toggleMemberAdmin,
    toggleMemberPremium,
    removeMember,
} = useOrganizationMembers(orgId, refreshOrg, memberCallbacks);

// Wrap toggleMemberAdmin to pass current user ID for self-demotion check (user view only)
function toggleMemberAdmin(member: OrganizationMemberRead) {
    return _toggleMemberAdmin(member, props.isAdminView ? undefined : auth.user?.id);
}

// Quota status (using shared composable)
const { isOverQuota, canAddPremium } = useOrganizationQuota(org);

// Subscription management (using shared composable)
const {
    showSubscribeModal,
    plans,
    isLoadingPlans,
    subscribingPriceId,
    openSubscribeModal,
    subscribeToPlan,
    openBillingPortal,
} = useOrganizationSubscription(orgId, org, refreshOrg);

// Stripe config
const config = useRuntimeConfig();

// Determine if subscription management buttons should be shown
// Admin view: always show if Stripe enabled
// User view: only show if self-service subscriptions are enabled
const canManageSubscription = computed(() => {
    const stripeEnabled = config.public.stripeEnabled;
    const selfServiceEnabled = String(config.public.orgSelfServiceSubscriptions) === 'true';
    return stripeEnabled && (props.isAdminView || selfServiceEnabled);
});

async function saveChanges() {
    isSaving.value = true;
    try {
        await api.patch(`/organizations/${orgId.value}`, form.value);
        showSuccess(t('core.organizations.updateSuccess'), t('core.organizations.updateSuccessDescription'));
        isEditing.value = false;
        refreshOrg();
    } catch (error: unknown) {
        showError(error, 'core.organizations.updateFailed');
    } finally {
        isSaving.value = false;
    }
}

async function deleteOrganization() {
    if (!org.value) return;

    const confirmed = await modal.open('confirm', {
        title: t('core.organizations.deleteTitle'),
        message: t('core.organizations.deleteConfirm', { name: org.value.name }),
        confirmText: t('core.common.delete'),
        confirmColor: 'error',
    });

    if (!confirmed) return;

    try {
        await api.delete(`/organizations/${orgId.value}`);
        showSuccess(t('core.organizations.deleteSuccess'));
        await router.push(props.backLink);
    } catch (error: unknown) {
        showError(error, 'core.organizations.deleteFailed');
    }
}

// Contact org admins (admin view only)
const showContactModal = ref(false);
const contactSubject = ref('');
const contactContent = ref('');
const isSendingContact = ref(false);

async function contactOrgAdmins() {
    if (!org.value) return;
    const adminIds = (org.value.members ?? []).filter((m) => m.is_admin).map((m) => m.user_id);
    if (!adminIds.length) return;

    isSendingContact.value = true;
    try {
        const conversation = await adminCreateConversation({
            subject: contactSubject.value,
            content: contactContent.value,
            participant_user_ids: adminIds,
        });
        showSuccess(t('core.organizations.contactSuccess'));
        showContactModal.value = false;
        contactSubject.value = '';
        contactContent.value = '';
        router.push(`/admin/messages/${conversation.id}`);
    } catch (error: unknown) {
        showError(error, 'core.organizations.contactFailed');
    } finally {
        isSendingContact.value = false;
    }
}

// Check for subscription success/cancel query params
onMounted(() => {
    if (route.query.subscription === 'success') {
        toast.add({
            title: t('core.organizations.subscriptionSuccess'),
            description: t('core.organizations.subscriptionSuccessDescription'),
            color: 'success',
            duration: 5000,
        });
        router.replace({ query: {} });
        refreshOrg();
    } else if (route.query.subscription === 'canceled') {
        toast.add({
            title: t('core.organizations.subscriptionCanceled'),
            description: t('core.organizations.subscriptionCanceledDescription'),
            color: 'warning',
            duration: 3000,
        });
        router.replace({ query: {} });
    }
});
</script>

<template>
    <div class="org-detail">
        <!-- Back link -->
        <NuxtLink :to="backLink" class="back-link">
            <UIcon name="i-lucide-arrow-left" />
            {{ backLinkText }}
        </NuxtLink>

        <!-- Loading state -->
        <div v-if="orgPending || !isAuthReady" class="loading">
            <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary-500" />
        </div>

        <!-- Access denied (user view only, after auth is ready) -->
        <template v-else-if="!isAdminView && (orgError || !isUserOrgAdmin)">
            <UAlert
                color="error"
                variant="subtle"
                icon="i-lucide-shield-x"
                :title="t('core.errors.forbidden')"
                :description="t('core.organizations.accessDenied')"
            />
        </template>

        <!-- Org not found -->
        <template v-else-if="!org">
            <UAlert
                color="error"
                variant="subtle"
                icon="i-lucide-building-2"
                :title="t('core.errors.notFound')"
                :description="t('core.organizations.notFound')"
            />
        </template>

        <template v-else>
            <!-- Header -->
            <div class="page-header">
                <div class="header-info">
                    <h1 class="page-title">{{ org.name }}</h1>
                    <span class="org-email">{{ org.email }}</span>
                    <div class="badges">
                        <UBadge
                            v-if="isAdminView && org.deleted_at"
                            :label="t('core.organizations.deleted')"
                            color="error"
                        />
                        <UBadge v-if="org.stripe_premium" :label="t('core.organizations.premium')" color="warning" />
                        <UBadge v-else-if="!isAdminView" :label="t('core.organizations.free')" color="neutral" />
                        <UBadge
                            v-if="isAdminView && isOverQuota"
                            :label="t('core.organizations.overQuota')"
                            color="error"
                        />
                        <UBadge
                            v-if="!isAdminView && org.stripe_premium"
                            :label="
                                t('core.organizations.seatsUsed', {
                                    used: org.premium_member_count,
                                    total: org.stripe_quota,
                                })
                            "
                            :color="isOverQuota ? 'error' : 'info'"
                        />
                    </div>
                </div>
                <div v-if="!org.deleted_at" class="header-actions">
                    <template v-if="canManageSubscription">
                        <UButton
                            v-if="org.stripe_premium"
                            :label="t('core.organizations.manageBilling')"
                            icon="i-lucide-credit-card"
                            color="neutral"
                            variant="outline"
                            @click="openBillingPortal"
                        />
                        <UButton
                            v-else
                            :label="t('core.organizations.subscribe')"
                            icon="i-lucide-sparkles"
                            color="primary"
                            @click="openSubscribeModal"
                        />
                    </template>
                    <UButton
                        v-if="isAdminView"
                        :label="t('core.organizations.contactAdmins')"
                        icon="i-lucide-message-square-plus"
                        color="neutral"
                        variant="outline"
                        @click="showContactModal = true"
                    />
                    <UButton
                        v-if="isAdminView"
                        :label="t('core.common.delete')"
                        icon="i-lucide-trash-2"
                        color="error"
                        variant="outline"
                        @click="deleteOrganization"
                    />
                </div>
            </div>

            <!-- Deleted org alert (admin view only) -->
            <UAlert
                v-if="isAdminView && org.deleted_at"
                color="error"
                variant="subtle"
                icon="i-lucide-trash-2"
                :title="t('core.organizations.deletedAlert')"
                :description="t('core.organizations.deletedAlertDescription', { date: formatDate(org.deleted_at) })"
                class="mb-6"
            />

            <!-- Over quota warning -->
            <UAlert
                v-if="isOverQuota"
                color="warning"
                variant="subtle"
                icon="i-lucide-alert-triangle"
                :title="t('core.organizations.quotaExceeded')"
                :description="
                    isAdminView
                        ? t('core.organizations.quotaExceededDescription', {
                              used: org.premium_member_count,
                              quota: org.stripe_quota,
                          })
                        : undefined
                "
                class="mb-6"
            />

            <div class="content-grid">
                <!-- Organization Info Card -->
                <OrganizationsInfoCard
                    v-model:form-name="form.name"
                    v-model:form-email="form.email"
                    v-model:form-description="form.description"
                    v-model:form-phone="form.phone"
                    v-model:form-tax-number="form.tax_number"
                    v-model:form-address-line1="form.address_line1"
                    v-model:form-address-line2="form.address_line2"
                    v-model:form-city="form.city"
                    v-model:form-state="form.state"
                    v-model:form-postal-code="form.postal_code"
                    v-model:form-country="form.country"
                    v-model:form-custom-data="form.custom_data"
                    :org="org"
                    :is-admin-view="isAdminView"
                    :is-editing="isEditing"
                    :is-saving="isSaving"
                    @start-edit="isEditing = true"
                    @cancel-edit="cancelEdit"
                    @save="saveChanges"
                />

                <!-- Members Card -->
                <OrganizationsMembersCard
                    v-model:show-add-member-modal="showAddMemberModal"
                    v-model:add-member-email="addMemberEmail"
                    v-model:add-member-as-admin="addMemberAsAdmin"
                    :org="org"
                    :is-admin-view="isAdminView"
                    :can-add-premium="canAddPremium"
                    :is-adding-member="isAddingMember"
                    @add-member="addMember"
                    @toggle-admin="toggleMemberAdmin"
                    @toggle-premium="toggleMemberPremium"
                    @remove-member="removeMember"
                />
            </div>
        </template>

        <!-- Contact Org Admins Modal -->
        <UModal v-model:open="showContactModal">
            <template #content>
                <UCard>
                    <template #header>
                        <UiModalHeader
                            :title="t('core.organizations.contactAdmins')"
                            @close="showContactModal = false"
                        />
                    </template>

                    <div class="flex flex-col gap-4">
                        <UFormField :label="t('core.organizations.contactSubject')">
                            <UInput v-model="contactSubject" class="w-full" />
                        </UFormField>
                        <UFormField :label="t('core.organizations.contactMessage')" required>
                            <UTextarea v-model="contactContent" :rows="5" class="w-full" />
                        </UFormField>
                    </div>

                    <template #footer>
                        <UiFormActions>
                            <UButton
                                color="neutral"
                                variant="outline"
                                :label="t('core.common.cancel')"
                                @click="showContactModal = false"
                            />
                            <UButton
                                :label="t('core.organizations.contactSend')"
                                :loading="isSendingContact"
                                :disabled="!contactSubject.trim() || !contactContent.trim()"
                                @click="contactOrgAdmins"
                            />
                        </UiFormActions>
                    </template>
                </UCard>
            </template>
        </UModal>

        <!-- Subscribe Modal -->
        <OrganizationsSubscriptionModal
            v-model:open="showSubscribeModal"
            :plans="plans"
            :is-loading="isLoadingPlans"
            :subscribing-price-id="subscribingPriceId"
            @subscribe="subscribeToPlan"
        />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.org-detail {
    @apply max-w-7xl mx-auto;
}

.back-link {
    @apply inline-flex items-center gap-2 text-gray-500 dark:text-gray-400 no-underline text-sm mb-4;
}

.back-link:hover {
    @apply text-primary-500;
}

.loading {
    @apply flex justify-center py-12;
}

.page-header {
    @apply flex justify-between items-start mb-6 flex-wrap gap-4;
}

.header-info {
    @apply flex flex-col gap-2;
}

.page-title {
    @apply text-2xl font-semibold m-0 text-gray-900 dark:text-gray-100;
}

.org-email {
    @apply text-gray-500 dark:text-gray-400;
}

.badges {
    @apply flex gap-2 flex-wrap;
}

.header-actions {
    @apply flex gap-2;
}

.content-grid {
    @apply flex flex-col gap-6;
}
</style>
