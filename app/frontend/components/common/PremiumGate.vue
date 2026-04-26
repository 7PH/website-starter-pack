<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/**
 * Markup-driven paywall wrapper for freemium content.
 *
 * Two named slots:
 *   - #teaser: always visible, SSR'd, indexable by Googlebot.
 *   - #gated: SSR'd so Googlebot can index it. Hidden client-side from
 *     non-premium users via hidden + aria-hidden + inert.
 *
 * For non-premium users, a paywall CTA renders below the (hidden) gated
 * section. The CTA wraps in <ClientOnly> so it never SSRs — premium
 * status is unknown at SSR time, and a server-rendered CTA would cause a
 * hydration mismatch for premium users.
 *
 * Emits a schema.org JSON-LD blob (`isAccessibleForFree: false` plus a
 * `hasPart` cssSelector pointing at the gated section) so Google's
 * flexible-sampling can index the content without flagging it as cloaking.
 *
 * The frontend gate is UX, not security. Real entitlement checks are
 * server-side: every premium write endpoint must depend on a
 * `require_premium` check (see CLAUDE.md).
 *
 * @example
 * <PremiumGate cta-to="/premium">
 *     <template #teaser>
 *         <h1>Lesson title</h1>
 *         <p>Intro paragraph.</p>
 *     </template>
 *     <template #gated>
 *         <FullLessonContent />
 *     </template>
 * </PremiumGate>
 */

interface Props {
    /** Stable id for the gated section. Auto-generated if omitted. */
    gatedId?: string;
    /** Heading for the paywall CTA card. Defaults to i18n key. */
    headline?: string;
    /** Body copy for the paywall CTA card. Defaults to i18n key. */
    body?: string;
    /** Label for the CTA button. Defaults to i18n key. */
    ctaLabel?: string;
    /** Where the CTA button navigates. Defaults to '/premium'. */
    ctaTo?: string;
    /** Suppress the schema.org JSON-LD emission. Set on demos or when the page already declares its own paywall structure. */
    noSchema?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    gatedId: undefined,
    headline: undefined,
    body: undefined,
    ctaLabel: undefined,
    ctaTo: '/premium',
    noSchema: false,
});

const { t } = useI18n();
const { isPremium } = usePremiumStatus();
const auth = useAuth();
const modal = useModalStore();

const generatedId = useId();
const resolvedGatedId = computed(() => props.gatedId ?? `premium-gate-${generatedId}`);

if (!props.noSchema) {
    useSchemaArticle({
        isAccessibleForFree: false,
        hasPart: {
            cssSelector: `#${resolvedGatedId.value}`,
            isAccessibleForFree: false,
        },
    });
}

async function onCtaClick() {
    if (!auth.isLoggedIn) {
        await modal.open('auth', {
            initialMode: 'signup',
            onSuccess: () => {
                // After successful auth, send still-non-premium users to the
                // billing/subscribe destination. Premium users see the gate
                // unlock automatically via reactivity — no navigation needed.
                if (!auth.user?.is_premium) {
                    navigateTo(props.ctaTo);
                }
            },
        });
        return;
    }
    navigateTo(props.ctaTo);
}
</script>

<template>
    <div class="premium-gate">
        <slot name="teaser" />

        <div
            :id="resolvedGatedId"
            :hidden="!isPremium"
            :aria-hidden="!isPremium || undefined"
            :inert="!isPremium || undefined"
        >
            <slot name="gated" />
        </div>

        <ClientOnly>
            <div
                v-if="!isPremium"
                class="mt-6 rounded-lg border border-primary-200 dark:border-primary-800 bg-primary-50 dark:bg-primary-950/40 p-6 text-center"
            >
                <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    {{ headline ?? t('core.premium.gate.headline') }}
                </h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-4 max-w-md mx-auto">
                    {{ body ?? t('core.premium.gate.body') }}
                </p>
                <UButton color="primary" icon="i-lucide-lock" @click="onCtaClick">
                    {{ ctaLabel ?? t('core.premium.gate.cta') }}
                </UButton>
            </div>
        </ClientOnly>
    </div>
</template>
