<script lang="ts" setup>
import LegalPage from '~/components/LegalPage.vue';

const { t } = useI18n();

useSeoMeta({
    title: () => t('core.legal.privacy'),
});
</script>

<template>
    <LegalPage :title="t('core.legal.privacy')" last-updated="January 2025">
        <h2>1. Information We Collect</h2>
        <p>We collect information you provide directly to us, including:</p>
        <ul>
            <li>Account information (email address, name)</li>
            <li>Usage data and preferences</li>
            <li>Communications you send to us</li>
        </ul>

        <h2>2. How We Use Your Information</h2>
        <p>We use the information we collect to:</p>
        <ul>
            <li>Provide and maintain our services</li>
            <li>Process transactions and send related information</li>
            <li>Send you technical notices and support messages</li>
            <li>Respond to your comments and questions</li>
            <li>Improve and develop new features</li>
        </ul>

        <h2>3. Information Sharing</h2>
        <p>
            We do not sell your personal information. We may share your information only in the following circumstances:
        </p>
        <ul>
            <li>With your consent</li>
            <li>To comply with legal obligations</li>
            <li>To protect our rights and prevent fraud</li>
            <li>With service providers who assist our operations</li>
        </ul>

        <h2>4. Data Security</h2>
        <p>
            We implement appropriate technical and organizational measures to protect your personal information against
            unauthorized access, alteration, disclosure, or destruction.
        </p>

        <h2>5. Your Rights</h2>
        <p>Depending on your location, you may have the right to:</p>
        <ul>
            <li>Access your personal data</li>
            <li>Correct inaccurate data</li>
            <li>Request deletion of your data</li>
            <li>Object to or restrict processing</li>
            <li>Data portability</li>
        </ul>

        <h2>6. Data Retention</h2>
        <p>
            We retain your information for as long as your account is active or as needed to provide you services. When
            you delete your account, we anonymize your personal data.
        </p>

        <h2>7. Changes to This Policy</h2>
        <p>
            We may update this privacy policy from time to time. We will notify you of any changes by updating the "Last
            updated" date.
        </p>

        <h2>8. Contact Us</h2>
        <p>If you have questions about this Privacy Policy, please contact us.</p>
    </LegalPage>
</template>
