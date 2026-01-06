<script lang="ts" setup>
import LegalPage from '~/components/LegalPage.vue';

const { t } = useI18n();

useSeoMeta({
    title: () => t('core.legal.cookies'),
});
</script>

<template>
    <LegalPage :title="t('core.legal.cookies')" last-updated="January 2025">
        <h2>1. What Are Cookies</h2>
        <p>
            Cookies are small text files stored on your device when you visit a website. They help the website remember
            your preferences and improve your browsing experience.
        </p>

        <h2>2. How We Use Cookies</h2>
        <p>We use cookies for the following purposes:</p>
        <ul>
            <li>
                <strong>Essential cookies:</strong> Required for the website to function properly (authentication,
                security)
            </li>
            <li><strong>Preference cookies:</strong> Remember your settings (language, theme)</li>
            <li><strong>Analytics cookies:</strong> Help us understand how visitors interact with our website</li>
        </ul>

        <h2>3. Types of Cookies We Use</h2>

        <h3>Essential Cookies</h3>
        <p>
            These cookies are necessary for the website to function and cannot be disabled. They are usually set in
            response to actions you take, such as logging in or filling out forms.
        </p>

        <h3>Analytics Cookies</h3>
        <p>
            We may use analytics services to collect anonymous information about how visitors use our site. This helps
            us improve our services.
        </p>

        <h2>4. Managing Cookies</h2>
        <p>
            Most web browsers allow you to control cookies through their settings. You can set your browser to refuse
            cookies or delete existing cookies. Note that disabling cookies may affect the functionality of our website.
        </p>

        <h2>5. Third-Party Cookies</h2>
        <p>
            Some cookies may be set by third-party services we use. We do not control these cookies. Please refer to the
            respective privacy policies of these services for more information.
        </p>

        <h2>6. Updates to This Policy</h2>
        <p>
            We may update this Cookie Policy from time to time. Any changes will be posted on this page with an updated
            "Last updated" date.
        </p>

        <h2>7. Contact Us</h2>
        <p>If you have questions about our use of cookies, please contact us.</p>
    </LegalPage>
</template>
