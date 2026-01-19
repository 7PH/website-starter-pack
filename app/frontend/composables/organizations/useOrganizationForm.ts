// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { Ref } from 'vue';

export interface OrganizationFormState {
    name: string;
    email: string;
    description: string;
    phone: string;
    tax_number: string;
    address_line1: string;
    address_line2: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
    custom_data: OrganizationCustomData;
}

/**
 * Composable for managing organization form state.
 * Handles form initialization, editing state, and reset functionality.
 */
export function useOrganizationForm(org: Ref<OrganizationRead | null | undefined>) {
    const form = ref<OrganizationFormState>({
        name: '',
        email: '',
        description: '',
        phone: '',
        tax_number: '',
        address_line1: '',
        address_line2: '',
        city: '',
        state: '',
        postal_code: '',
        country: '',
        custom_data: {} as OrganizationCustomData,
    });

    const isEditing = ref(false);
    const isSaving = ref(false);

    // Initialize form from org data
    function initializeForm(orgData: OrganizationRead | null | undefined) {
        if (orgData) {
            form.value = {
                name: orgData.name,
                email: orgData.email,
                description: orgData.description || '',
                phone: orgData.phone || '',
                tax_number: orgData.tax_number || '',
                address_line1: orgData.address_line1 || '',
                address_line2: orgData.address_line2 || '',
                city: orgData.city || '',
                state: orgData.state || '',
                postal_code: orgData.postal_code || '',
                country: orgData.country || '',
                custom_data: (orgData.custom_data as OrganizationCustomData) || ({} as OrganizationCustomData),
            };
        }
    }

    // Reset form to org data and cancel editing
    function cancelEdit() {
        initializeForm(org.value);
        isEditing.value = false;
    }

    // Watch org changes to initialize form
    watch(org, initializeForm, { immediate: true });

    return {
        form,
        isEditing,
        isSaving,
        cancelEdit,
        initializeForm,
    };
}
