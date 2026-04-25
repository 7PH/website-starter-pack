<script setup lang="ts">
const api = useApi();
const { t } = useI18n();
const modal = useModalStore();

const apiStatus = ref<'loading' | 'online' | 'offline'>('loading');

onMounted(async () => {
    try {
        await api.get('/healthcheck');
        apiStatus.value = 'online';
    } catch {
        apiStatus.value = 'offline';
    }
});

const stack = ['nuxt 3', 'fastapi', 'postgres', 'tailwind', 'pinia', 'traefik'];

const features = computed(() => [
    {
        key: 'auth',
        area: 'auth',
        icon: 'i-lucide-shield-check',
        title: t('core.home.features.auth'),
        description: t('core.home.features.authDescription'),
    },
    {
        key: 'payments',
        area: 'billing',
        icon: 'i-lucide-credit-card',
        title: t('core.home.features.payments'),
        description: t('core.home.features.paymentsDescription'),
    },
    {
        key: 'organizations',
        area: 'orgs',
        icon: 'i-lucide-users',
        title: t('core.home.features.organizations'),
        description: t('core.home.features.organizationsDescription'),
    },
    {
        key: 'i18n',
        area: 'i18n',
        icon: 'i-lucide-globe',
        title: t('core.home.features.i18n'),
        description: t('core.home.features.i18nDescription'),
    },
]);

function getStarted() {
    modal.open('auth', { initialMode: 'signup' });
}

function signIn() {
    modal.open('auth', { initialMode: 'login' });
}
</script>

<template>
    <div class="hero">
        <div class="hero-bg" aria-hidden="true" />
        <div class="hero-grid">
            <!-- Left: copy + CTAs -->
            <div class="hero-copy">
                <UiAnimateFadeUp>
                    <div class="eyebrow">
                        <span class="eyebrow-dot" />
                        {{ t('core.home.eyebrow') }}
                    </div>
                </UiAnimateFadeUp>

                <UiAnimateFadeUp :delay="80">
                    <h1 class="headline">
                        {{ t('core.home.headline') }}
                    </h1>
                </UiAnimateFadeUp>

                <UiAnimateFadeUp :delay="160">
                    <p class="subtitle">{{ t('core.home.subtitle') }}</p>
                </UiAnimateFadeUp>

                <UiAnimateFadeUp :delay="240">
                    <div class="cta-row">
                        <UiGradientButton size="lg" @click="getStarted">
                            {{ t('core.home.getStarted') }}
                            <UIcon name="i-lucide-arrow-right" />
                        </UiGradientButton>
                        <button type="button" class="cta-secondary" @click="signIn">
                            {{ t('core.home.signIn') }}
                        </button>
                    </div>
                </UiAnimateFadeUp>

                <UiAnimateFadeUp :delay="320">
                    <div class="stack-strip">
                        <span v-for="(name, i) in stack" :key="name" class="stack-item">
                            {{ name }}<span v-if="i < stack.length - 1" class="stack-sep"> · </span>
                        </span>
                    </div>
                </UiAnimateFadeUp>
            </div>

            <!-- Right: terminal panel -->
            <UiAnimateFadeUp :delay="120" class="terminal-wrap">
                <div class="terminal" role="img" aria-label="Terminal output showing dev server starting">
                    <div class="terminal-chrome">
                        <span class="dot dot-r" />
                        <span class="dot dot-y" />
                        <span class="dot dot-g" />
                        <span class="terminal-title">~/website-starter</span>
                    </div>
                    <div class="terminal-body">
                        <div class="line">
                            <span class="prompt">$</span>
                            <span class="cmd">npm run dev</span>
                        </div>
                        <div class="line">
                            <span class="ok">✓</span>
                            <span class="svc">frontend</span>
                            <span class="muted">ready on</span>
                            <span class="port">:3000</span>
                        </div>
                        <div class="line">
                            <span class="ok">✓</span>
                            <span class="svc">backend</span>
                            <span class="muted">ready on</span>
                            <span class="port">:8000</span>
                        </div>
                        <div class="line">
                            <span class="ok">✓</span>
                            <span class="svc">traefik</span>
                            <span class="muted">routing</span>
                            <span class="port">:80</span>
                        </div>
                        <div class="line">
                            <template v-if="apiStatus === 'loading'">
                                <span class="spinner">⠋</span>
                                <span class="svc">postgres</span>
                                <span class="muted">probing /api/v1/healthcheck…</span>
                            </template>
                            <template v-else-if="apiStatus === 'online'">
                                <span class="ok">✓</span>
                                <span class="svc">postgres</span>
                                <span class="muted">healthy</span>
                            </template>
                            <template v-else>
                                <span class="err">✗</span>
                                <span class="svc">postgres</span>
                                <span class="muted">unreachable</span>
                            </template>
                        </div>
                        <div class="line caret-line">
                            <span class="prompt">$</span>
                            <span class="caret" />
                        </div>
                    </div>
                </div>
            </UiAnimateFadeUp>
        </div>
    </div>

    <!-- Features bento -->
    <section class="bento-section">
        <div class="bento">
            <UiAnimateOnScroll
                v-for="(feature, index) in features"
                :key="feature.key"
                animation="fade-up"
                :delay="index * 80"
                :class="['bento-cell', `cell-${feature.area}`]"
            >
                <article class="card">
                    <header class="card-head">
                        <span class="card-icon">
                            <UIcon :name="feature.icon" />
                        </span>
                        <h3 class="card-title">{{ feature.title }}</h3>
                    </header>
                    <p class="card-desc">{{ feature.description }}</p>

                    <!-- Per-card visual peek -->
                    <div v-if="feature.area === 'auth'" class="peek peek-auth">
                        <div class="mock-input">
                            <span class="mock-label">email</span>
                            <span class="mock-value">you@studio.dev</span>
                        </div>
                        <div class="mock-input">
                            <span class="mock-label">password</span>
                            <span class="mock-value">••••••••••</span>
                        </div>
                        <div class="mock-btn">Continue</div>
                        <div class="mock-or"><span>or</span></div>
                        <div class="mock-oauth"><UIcon name="i-lucide-chrome" /> Google</div>
                    </div>

                    <div v-else-if="feature.area === 'billing'" class="peek peek-billing">
                        <div class="price">
                            <span class="price-currency">$</span>
                            <span class="price-amount">9</span>
                            <span class="price-cycle">/ mo</span>
                        </div>
                        <div class="price-chip">Pro</div>
                    </div>

                    <div v-else-if="feature.area === 'orgs'" class="peek peek-orgs">
                        <div class="member">
                            <span class="avatar avatar-a">A</span>
                            <span class="member-name">Alice</span>
                            <span class="role role-owner">Owner</span>
                        </div>
                        <div class="member">
                            <span class="avatar avatar-b">B</span>
                            <span class="member-name">Bob</span>
                            <span class="role">Member</span>
                        </div>
                    </div>

                    <div v-else-if="feature.area === 'i18n'" class="peek peek-i18n">
                        <div class="json-col">
                            <div class="json-head">en.json</div>
                            <pre><span class="k">"save"</span>: <span class="s">"Save"</span>,
<span class="k">"cancel"</span>: <span class="s">"Cancel"</span></pre>
                        </div>
                        <div class="json-col">
                            <div class="json-head">fr.json</div>
                            <pre><span class="k">"save"</span>: <span class="s">"Enregistrer"</span>,
<span class="k">"cancel"</span>: <span class="s">"Annuler"</span></pre>
                        </div>
                    </div>
                </article>
            </UiAnimateOnScroll>
        </div>
    </section>
</template>

<style scoped>
@reference "~/assets/css/main.css";

/* ────────────────────────────────────────────────────────────
 * HERO
 * ──────────────────────────────────────────────────────────── */
.hero {
    @apply relative px-4 sm:px-6 lg:px-10 pt-12 pb-16 sm:pt-16 sm:pb-20;
    @apply overflow-hidden;
}

.hero-bg {
    @apply absolute inset-0 pointer-events-none;
    background:
        radial-gradient(ellipse 80% 50% at 20% 0%, rgba(var(--theme-brand-rgb), 0.12), transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 30%, rgba(var(--theme-accent-rgb), 0.1), transparent 60%);
}
.hero-bg::after {
    content: '';
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(120, 134, 161, 0.2) 1px, transparent 1px);
    background-size: 22px 22px;
    mask-image: radial-gradient(ellipse 70% 60% at 50% 30%, black 30%, transparent 75%);
    -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 30%, black 30%, transparent 75%);
    opacity: 0.5;
}

.hero-grid {
    @apply relative max-w-6xl mx-auto;
    @apply grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center;
}

.hero-copy {
    @apply lg:col-span-5;
}

/* Eyebrow */
.eyebrow {
    @apply inline-flex items-center gap-2 mb-5;
    @apply font-mono text-[11px] uppercase tracking-[0.18em];
    @apply text-slate-500 dark:text-slate-400;
}
.eyebrow-dot {
    @apply w-1.5 h-1.5 rounded-full;
    background: rgb(var(--theme-accent-rgb));
    box-shadow: 0 0 8px rgba(var(--theme-accent-rgb), 0.7);
}

/* Headline */
.headline {
    @apply text-4xl sm:text-5xl lg:text-[3.5rem] font-bold leading-[1.05] tracking-tight;
    @apply text-slate-900 dark:text-white;
    @apply mb-5;
}

.subtitle {
    @apply text-base sm:text-lg text-slate-600 dark:text-slate-400 mb-8 max-w-md;
}

/* CTAs */
.cta-row {
    @apply flex flex-wrap items-center gap-3 mb-10;
}
.cta-secondary {
    @apply inline-flex items-center gap-2 px-5 py-3 rounded-lg cursor-pointer;
    @apply text-sm font-medium;
    @apply text-slate-700 dark:text-slate-200;
    @apply border border-slate-300 dark:border-slate-700;
    @apply bg-white/60 dark:bg-slate-900/40;
    @apply hover:border-slate-400 dark:hover:border-slate-500;
    @apply transition-colors duration-150;
}

/* Stack wordmark strip */
.stack-strip {
    @apply font-mono text-xs text-slate-500 dark:text-slate-500;
    @apply flex flex-wrap items-center gap-x-2 gap-y-1;
}
.stack-item {
    @apply tracking-tight;
}
.stack-sep {
    @apply text-slate-400 dark:text-slate-600;
}

/* ────────────────────────────────────────────────────────────
 * TERMINAL
 * ──────────────────────────────────────────────────────────── */
.terminal-wrap {
    @apply lg:col-span-7;
}
.terminal {
    @apply rounded-xl overflow-hidden;
    @apply bg-slate-950 border border-slate-800;
    box-shadow:
        0 30px 80px -20px rgba(8, 8, 25, 0.5),
        0 0 0 1px rgba(148, 163, 184, 0.06),
        inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
.terminal-chrome {
    @apply flex items-center gap-2 px-4 py-3;
    @apply border-b border-slate-800/80 bg-slate-900/60;
}
.dot {
    @apply w-3 h-3 rounded-full;
}
.dot-r {
    background: #ef4444;
}
.dot-y {
    background: #eab308;
}
.dot-g {
    background: #22c55e;
}
.terminal-title {
    @apply ml-3 font-mono text-xs text-slate-500;
}

.terminal-body {
    @apply px-5 py-5 font-mono text-sm leading-7;
    @apply text-slate-300;
}
.line {
    @apply flex items-center gap-2 whitespace-nowrap;
}
.prompt {
    color: rgb(var(--theme-accent-rgb));
}
.cmd {
    @apply text-slate-100;
}
.ok {
    @apply text-emerald-400;
}
.err {
    @apply text-rose-400;
}
.spinner {
    @apply text-amber-400;
    animation: spin-glyph 1s steps(8, end) infinite;
    display: inline-block;
}
.svc {
    @apply text-slate-200 inline-block min-w-[68px];
}
.muted {
    @apply text-slate-500;
}
.port {
    color: rgb(var(--theme-pop-rgb));
    @apply opacity-90;
}

.caret-line {
    @apply mt-1;
}
.caret {
    @apply inline-block w-2 h-4 align-middle;
    background: rgb(var(--theme-accent-rgb));
    animation: caret-blink 1.1s steps(2, jump-none) infinite;
}

@keyframes caret-blink {
    0%,
    60% {
        opacity: 1;
    }
    61%,
    100% {
        opacity: 0;
    }
}
@keyframes spin-glyph {
    0% {
        content: '⠋';
    }
    100% {
        transform: rotate(360deg);
    }
}

/* ────────────────────────────────────────────────────────────
 * BENTO
 * ──────────────────────────────────────────────────────────── */
.bento-section {
    @apply px-4 sm:px-6 lg:px-10 pb-20;
}
.bento {
    @apply relative max-w-6xl mx-auto;
    @apply grid gap-4;
    grid-template-columns: 1fr;
    grid-template-areas:
        'auth'
        'billing'
        'orgs'
        'i18n';
}

@media (min-width: 1024px) {
    .bento {
        grid-template-columns: 1.15fr 1fr;
        grid-template-rows: auto auto auto;
        grid-template-areas:
            'auth    billing'
            'auth    orgs'
            'i18n    i18n';
    }
}

.cell-auth {
    grid-area: auth;
}
.cell-billing {
    grid-area: billing;
}
.cell-orgs {
    grid-area: orgs;
}
.cell-i18n {
    grid-area: i18n;
}

.card {
    @apply relative h-full p-5 sm:p-6 rounded-xl;
    @apply bg-white dark:bg-slate-900/60;
    @apply border border-slate-200 dark:border-slate-800;
    @apply transition-colors duration-200;
    @apply flex flex-col;
}
.card:hover {
    @apply border-slate-300 dark:border-slate-700;
}

.card-head {
    @apply flex items-center gap-3 mb-2;
}
.card-icon {
    @apply inline-flex items-center justify-center w-9 h-9 rounded-md;
    @apply bg-slate-100 dark:bg-slate-800/80;
    @apply text-slate-700 dark:text-slate-300;
    font-size: 18px;
}
.card-title {
    @apply text-base font-semibold text-slate-900 dark:text-slate-100;
}
.card-desc {
    @apply text-sm text-slate-600 dark:text-slate-400 mb-5;
}

/* ─── Auth peek ─────────────────────────── */
.peek-auth {
    @apply mt-auto p-4 rounded-lg;
    @apply bg-slate-50 dark:bg-slate-950/60;
    @apply border border-slate-200/80 dark:border-slate-800/80;
    @apply font-mono text-xs;
}
.mock-input {
    @apply flex items-center justify-between px-3 py-2 rounded-md mb-2;
    @apply bg-white dark:bg-slate-900;
    @apply border border-slate-200 dark:border-slate-800;
}
.mock-label {
    @apply text-slate-500;
}
.mock-value {
    @apply text-slate-700 dark:text-slate-300;
}
.mock-btn {
    @apply text-center py-2 rounded-md text-white text-[11px] font-semibold tracking-wide;
    background: var(--gradient-brand);
    background-size: 200% 200%;
}
.mock-or {
    @apply relative my-3 text-center text-[10px] text-slate-400;
}
.mock-or::before {
    content: '';
    @apply absolute top-1/2 left-0 w-[40%] h-px bg-slate-200 dark:bg-slate-800;
}
.mock-or::after {
    content: '';
    @apply absolute top-1/2 right-0 w-[40%] h-px bg-slate-200 dark:bg-slate-800;
}
.mock-oauth {
    @apply flex items-center justify-center gap-2 py-2 rounded-md;
    @apply border border-slate-200 dark:border-slate-800;
    @apply text-slate-700 dark:text-slate-300;
}

/* ─── Billing peek ──────────────────────── */
.peek-billing {
    @apply mt-auto flex items-end justify-between p-5 rounded-lg;
    @apply bg-slate-50 dark:bg-slate-950/60;
    @apply border border-slate-200/80 dark:border-slate-800/80;
}
.price {
    @apply flex items-baseline;
    @apply text-slate-900 dark:text-white;
}
.price-currency {
    @apply text-xl font-semibold text-slate-500;
    @apply mr-0.5;
}
.price-amount {
    @apply text-5xl font-bold tracking-tight;
}
.price-cycle {
    @apply ml-2 text-sm text-slate-500;
}
.price-chip {
    @apply px-2.5 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider;
    @apply text-violet-700 dark:text-violet-300;
    background: rgba(var(--theme-brand-rgb), 0.12);
}

/* ─── Orgs peek ─────────────────────────── */
.peek-orgs {
    @apply mt-auto p-3 rounded-lg space-y-2;
    @apply bg-slate-50 dark:bg-slate-950/60;
    @apply border border-slate-200/80 dark:border-slate-800/80;
}
.member {
    @apply flex items-center gap-3 px-3 py-2 rounded-md;
    @apply bg-white dark:bg-slate-900;
    @apply border border-slate-200/70 dark:border-slate-800;
}
.avatar {
    @apply w-7 h-7 rounded-full flex items-center justify-center;
    @apply text-xs font-semibold text-white;
}
.avatar-a {
    background: linear-gradient(135deg, rgb(var(--theme-brand-rgb)), rgb(var(--theme-pop-rgb)));
}
.avatar-b {
    background: linear-gradient(135deg, rgb(var(--theme-accent-rgb)), rgb(var(--theme-brand-rgb)));
}
.member-name {
    @apply flex-1 text-sm text-slate-700 dark:text-slate-300;
}
.role {
    @apply text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded;
    @apply bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400;
}
.role-owner {
    @apply text-violet-700 dark:text-violet-300;
    background: rgba(var(--theme-brand-rgb), 0.12);
}

/* ─── i18n peek ─────────────────────────── */
.peek-i18n {
    @apply mt-auto grid grid-cols-2 gap-3 p-4 rounded-lg;
    @apply bg-slate-50 dark:bg-slate-950/60;
    @apply border border-slate-200/80 dark:border-slate-800/80;
}
.json-col {
    @apply min-w-0;
}
.json-head {
    @apply font-mono text-[10px] uppercase tracking-wider mb-2;
    @apply text-slate-500;
}
.peek-i18n pre {
    @apply font-mono text-xs leading-6 m-0 whitespace-pre-wrap;
    @apply text-slate-600 dark:text-slate-400;
}
.peek-i18n .k {
    color: rgb(var(--theme-accent-rgb));
}
.peek-i18n .s {
    color: rgb(var(--theme-pop-rgb));
}
</style>
