<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatDate, initials } from '~/utils/formatters';
import { useOrganizationMembers, useOrganizationQuota } from '~/composables/organizations/useOrganizationMembers';
import { useOrganizationSubscription } from '~/composables/organizations/useOrganizationSubscription';
import { useOrganizationForm } from '~/composables/organizations/useOrganizationForm';
import { adminCreateConversation } from '~/utils/api/conversations';

export interface OrganizationDetailProps {
    isAdminView?: boolean;
    backLink: string;
    backLinkText: string;
}

const props = withDefaults(defineProps<OrganizationDetailProps>(), {
    isAdminView: false,
});

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const api = useApi();
const modal = useModalStore();
const { t } = useI18n();
const { showSuccess, showWarning, showError } = useToastHelpers();

const orgId = computed(() => Number(route.params.id));

const isAuthReady = computed(() => props.isAdminView || (auth.isLoggedIn && auth.user !== null));

const membership = computed(() => {
    if (props.isAdminView) return null;
    const user = auth.user as UserRead | null;
    return user?.organizations?.find((o: UserOrganizationInfo) => o.organization_id === orgId.value) ?? null;
});

const isMember = computed(() => props.isAdminView || membership.value !== null);
const isOwner = computed(() => props.isAdminView || membership.value?.is_admin === true);

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

const { form, isEditing, isSaving, cancelEdit } = useOrganizationForm(org);

const memberCallbacks = props.isAdminView
    ? undefined
    : {
          onSelfDemoted: async () => {
              await auth.refreshToken();
              router.push('/account?tab=organizations');
          },
          onAuthRefreshNeeded: () => auth.refreshToken(),
      };

const {
    showAddMemberModal,
    isAddingMember,
    inviteMember,
    toggleMemberAdmin: _toggleMemberAdmin,
    toggleMemberPremium,
    removeMember,
} = useOrganizationMembers(orgId, refreshOrg, memberCallbacks);

function toggleMemberAdmin(member: OrganizationMemberRead) {
    return _toggleMemberAdmin(member, props.isAdminView ? undefined : auth.user?.id);
}

const { isOverQuota, canAddPremium } = useOrganizationQuota(org);

const {
    showSubscribeModal,
    plans,
    isLoadingPlans,
    subscribingPriceId,
    openSubscribeModal,
    subscribeToPlan,
    openBillingPortal,
} = useOrganizationSubscription(orgId, org, refreshOrg);

const config = useRuntimeConfig();

const canManageSubscription = computed(() => {
    const stripeEnabled = config.public.stripeEnabled;
    const selfServiceEnabled = String(config.public.orgSelfServiceSubscriptions) === 'true';
    return stripeEnabled && (props.isAdminView || selfServiceEnabled);
});

// Tabs: Overview + Members visible to any member; Billing + Settings owner-only.
// Billing is hidden for owners when self-service is off (they can't act on anything there).
const availableTabs = computed(() => {
    const tabs = [
        { value: 'overview', label: t('core.organizations.tabs.overview'), icon: 'i-lucide-layout-grid' },
        { value: 'members', label: t('core.organizations.tabs.members'), icon: 'i-lucide-users' },
    ];
    if (isOwner.value) {
        if (canManageSubscription.value) {
            tabs.push({
                value: 'billing',
                label: t('core.organizations.tabs.billing'),
                icon: 'i-lucide-credit-card',
            });
        }
        if (props.isAdminView && config.public.stripeEnabled) {
            tabs.push({
                value: 'admin-billing',
                label: t('core.organizations.tabs.adminBilling'),
                icon: 'i-lucide-landmark',
            });
        }
        tabs.push({ value: 'settings', label: t('core.organizations.tabs.settings'), icon: 'i-lucide-settings' });
    }
    return tabs;
});

const activeTab = computed({
    get: () => {
        const tabParam = route.query.tab as string;
        const valid = availableTabs.value.find((t) => t.value === tabParam);
        return valid ? tabParam : availableTabs.value[0]?.value || 'overview';
    },
    set: (value: string) => {
        router.replace({ query: { ...route.query, tab: value } });
    },
});

function onTabChange(key: string | number) {
    activeTab.value = String(key);
}

function goToTab(tab: string) {
    activeTab.value = tab;
}

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

// Contact Owners modal (admin view only)
const showContactModal = ref(false);
const contactSubject = ref('');
const contactContent = ref('');
const isSendingContact = ref(false);

async function contactOrgOwners() {
    if (!org.value) return;
    const ownerIds = (org.value.members ?? []).filter((m) => m.is_admin).map((m) => m.user_id);
    if (!ownerIds.length) return;
    isSendingContact.value = true;
    try {
        const conversation = await adminCreateConversation({
            subject: contactSubject.value,
            content: contactContent.value,
            participant_user_ids: ownerIds,
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

onMounted(() => {
    if (route.query.subscription === 'success') {
        showSuccess(
            t('core.organizations.subscriptionSuccess'),
            t('core.organizations.subscriptionSuccessDescription'),
        );
        router.replace({ query: { tab: activeTab.value } });
        refreshOrg();
    } else if (route.query.subscription === 'canceled') {
        showWarning(
            t('core.organizations.subscriptionCanceled'),
            t('core.organizations.subscriptionCanceledDescription'),
        );
        router.replace({ query: { tab: activeTab.value } });
    }
});
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <NuxtLink
            :to="backLink"
            class="flex items-center gap-1.5 self-start text-[13px] font-bold text-muted hover:text-highlighted"
        >
            <UIcon name="i-lucide-arrow-left" />
            {{ backLinkText }}
        </NuxtLink>

        <div v-if="orgPending || !isAuthReady" class="flex justify-center py-12">
            <UIcon name="i-lucide-loader-2" class="size-8 animate-spin text-primary" />
        </div>

        <template v-else-if="!isAdminView && (orgError || !isMember)">
            <UAlert
                color="error"
                variant="subtle"
                icon="i-lucide-shield-x"
                :title="t('core.errors.forbidden')"
                :description="t('core.organizations.accessDenied')"
            />
        </template>

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
            <div class="flex flex-wrap items-center gap-4">
                <span
                    class="flex size-13 shrink-0 items-center justify-center rounded-xl bg-primary-100 text-lg font-extrabold text-primary-700 md:size-15 dark:bg-primary-500/20 dark:text-primary-300"
                >
                    {{ initials(org.name) }}
                </span>
                <div class="flex min-w-45 flex-1 flex-col gap-1">
                    <h1 class="text-[22px] font-extrabold tracking-[-0.01em] text-highlighted md:text-[26px]">
                        {{ org.name }}
                    </h1>
                    <span class="text-sm text-muted">
                        {{ t('core.organizations.contactEmail') }}: {{ org.email }}
                    </span>
                    <div class="mt-1 flex flex-wrap gap-1.5">
                        <UBadge
                            v-if="isAdminView && org.deleted_at"
                            :label="t('core.organizations.deleted')"
                            color="error"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            :label="isOwner ? t('core.organizations.admin') : t('core.organizations.member')"
                            :color="isOwner ? 'info' : 'neutral'"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="org.stripe_premium"
                            :label="t('core.organizations.premium')"
                            color="warning"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-else-if="!isAdminView"
                            :label="t('core.organizations.free')"
                            color="neutral"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="isAdminView && isOverQuota"
                            :label="t('core.organizations.overQuota')"
                            color="error"
                            variant="soft"
                            class="rounded-full"
                        />
                    </div>
                </div>
                <div v-if="isAdminView && !org.deleted_at" class="flex flex-wrap gap-2">
                    <UButton
                        v-if="org.stripe_dashboard_url"
                        :to="org.stripe_dashboard_url"
                        target="_blank"
                        :label="t('core.organizations.openInStripe')"
                        icon="i-lucide-external-link"
                        size="lg"
                        color="neutral"
                        variant="outline"
                    />
                    <UButton
                        :label="t('core.organizations.contactAdmins')"
                        icon="i-lucide-message-square-plus"
                        size="lg"
                        color="neutral"
                        variant="outline"
                        @click="showContactModal = true"
                    />
                </div>
            </div>

            <UAlert
                v-if="isAdminView && org.deleted_at"
                color="error"
                variant="subtle"
                icon="i-lucide-trash-2"
                :title="t('core.organizations.deletedAlert')"
                :description="t('core.organizations.deletedAlertDescription', { date: formatDate(org.deleted_at) })"
            />

            <UTabs
                :items="availableTabs"
                :model-value="activeTab"
                variant="link"
                :content="false"
                @update:model-value="onTabChange"
            />

            <!-- Tab content -->
            <OrganizationsOverviewTab
                v-if="activeTab === 'overview'"
                :org="org"
                :is-owner="isOwner"
                :is-admin-view="isAdminView"
                :can-manage-subscription="canManageSubscription"
                @go-to-tab="goToTab"
            />

            <OrganizationsMembersCard
                v-else-if="activeTab === 'members'"
                v-model:show-add-member-modal="showAddMemberModal"
                :org="org"
                :is-admin-view="isAdminView"
                :is-owner="isOwner"
                :can-add-premium="canAddPremium"
                :is-adding-member="isAddingMember"
                :current-user-id="auth.user?.id"
                @invite="inviteMember"
                @toggle-admin="toggleMemberAdmin"
                @toggle-premium="toggleMemberPremium"
                @remove-member="removeMember"
            />

            <OrganizationsBillingTab
                v-else-if="activeTab === 'billing' && isOwner"
                :org="org"
                :can-manage-subscription="canManageSubscription"
                :is-admin-view="isAdminView"
                @open-subscribe-modal="openSubscribeModal"
                @open-billing-portal="openBillingPortal"
            />

            <OrganizationsAdminBillingTab
                v-else-if="activeTab === 'admin-billing' && isAdminView && isOwner"
                :org-id="orgId"
            />

            <div v-else-if="activeTab === 'settings' && isOwner" class="flex flex-col gap-4">
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
                <section
                    v-if="isAdminView && !org.deleted_at"
                    class="flex flex-col items-start gap-2.5 rounded-xl border border-error/30 px-4.5 py-3.5"
                >
                    <h2 class="text-[15px] font-extrabold text-error">{{ t('core.organizations.deleteTitle') }}</h2>
                    <UButton
                        :label="t('core.common.delete')"
                        icon="i-lucide-trash-2"
                        color="error"
                        variant="outline"
                        @click="deleteOrganization"
                    />
                </section>
            </div>
        </template>

        <!-- Contact Owners Modal -->
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
                                @click="contactOrgOwners"
                            />
                        </UiFormActions>
                    </template>
                </UCard>
            </template>
        </UModal>

        <OrganizationsSubscriptionModal
            v-model:open="showSubscribeModal"
            :plans="plans"
            :is-loading="isLoadingPlans"
            :subscribing-price-id="subscribingPriceId"
            @subscribe="subscribeToPlan"
        />
    </div>
</template>
