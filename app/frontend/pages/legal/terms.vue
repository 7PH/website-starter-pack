<script lang="ts" setup>
import LegalPage from '~/components/LegalPage.vue';

const { t } = useI18n();

useSeoMeta({
    title: () => t('core.legal.terms'),
});
</script>

<template>
    <LegalPage :title="t('core.legal.terms')" last-updated="January 2025">
        <h2>1. Acceptance of Terms</h2>
        <p>
            By accessing and using this website, you accept and agree to be bound by these Terms of Service. If you do
            not agree to these terms, please do not use our services.
        </p>

        <h2>2. Use of Service</h2>
        <p>
            You agree to use our services only for lawful purposes and in accordance with these Terms. You agree not to:
        </p>
        <ul>
            <li>Use the service in any way that violates applicable laws or regulations</li>
            <li>Attempt to gain unauthorized access to any part of the service</li>
            <li>Interfere with or disrupt the service or servers</li>
            <li>Transmit any malicious code or harmful content</li>
        </ul>

        <h2>3. User Accounts</h2>
        <p>
            When you create an account, you are responsible for maintaining the security of your account credentials.
            You agree to notify us immediately of any unauthorized access to your account.
        </p>

        <h2>4. Intellectual Property</h2>
        <p>
            All content and materials available on this service are protected by intellectual property laws. You may not
            copy, modify, distribute, or create derivative works without our prior written consent.
        </p>

        <h2>5. Limitation of Liability</h2>
        <p>
            To the fullest extent permitted by law, we shall not be liable for any indirect, incidental, special, or
            consequential damages arising from your use of our services.
        </p>

        <h2>6. Changes to Terms</h2>
        <p>
            We reserve the right to modify these terms at any time. We will notify users of any material changes by
            updating the "Last updated" date. Your continued use of the service constitutes acceptance of the modified
            terms.
        </p>

        <h2>7. Contact</h2>
        <p>If you have any questions about these Terms of Service, please contact us.</p>
    </LegalPage>
</template>
