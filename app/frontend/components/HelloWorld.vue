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

const techStack = [
    { name: 'Nuxt 3', icon: 'i-lucide-monitor', color: 'accent' },
    { name: 'FastAPI', icon: 'i-lucide-zap', color: 'primary' },
    { name: 'PostgreSQL', icon: 'i-lucide-database', color: 'pop' },
    { name: 'Tailwind', icon: 'i-lucide-palette', color: 'accent' },
];

const features = [
    {
        icon: 'i-lucide-shield-check',
        title: 'Authentication',
        description: 'Built-in auth with email/password and social logins',
    },
    {
        icon: 'i-lucide-credit-card',
        title: 'Payments',
        description: 'Stripe integration for subscriptions and billing',
    },
    { icon: 'i-lucide-users', title: 'Organizations', description: 'Multi-tenant support with team management' },
    {
        icon: 'i-lucide-globe',
        title: 'i18n Ready',
        description: 'Internationalization with English and French included',
    },
];
</script>

<template>
    <div class="hero-container">
        <!-- Decorative blobs -->
        <div class="blob blob-1" />
        <div class="blob blob-2" />

        <div class="hero-content">
            <UiAnimateFadeUp>
                <h1 class="hero-title text-gradient-brand">Website Starter Pack</h1>
            </UiAnimateFadeUp>

            <UiAnimateFadeUp :delay="100">
                <p class="hero-subtitle">
                    Full-stack web application template with Nuxt 3, FastAPI, PostgreSQL, and Traefik.
                </p>
            </UiAnimateFadeUp>

            <!-- Tech Stack Badges -->
            <UiAnimateFadeUp :delay="200">
                <div class="tech-badges">
                    <span v-for="tech in techStack" :key="tech.name" :class="['tech-badge', tech.color]">
                        <UIcon :name="tech.icon" />
                        {{ tech.name }}
                    </span>
                </div>
            </UiAnimateFadeUp>

            <!-- CTA Button -->
            <UiAnimateFadeUp :delay="300">
                <div class="cta-section">
                    <UiGradientButton size="lg" @click="modal.open('auth', { initialMode: 'signup' })">
                        <UIcon name="i-lucide-arrow-right" class="mr-2" />
                        Get Started
                    </UiGradientButton>
                </div>
            </UiAnimateFadeUp>

            <!-- API Status -->
            <UiAnimateFadeUp :delay="400">
                <div class="api-status">
                    <span
                        class="status-dot"
                        :class="{
                            online: apiStatus === 'online',
                            offline: apiStatus === 'offline',
                            loading: apiStatus === 'loading',
                        }"
                    />
                    <span class="status-text">
                        API
                        {{ apiStatus === 'online' ? 'Connected' : apiStatus === 'offline' ? 'Offline' : 'Checking...' }}
                    </span>
                </div>
            </UiAnimateFadeUp>
        </div>
    </div>

    <!-- Features Section (showcases AnimateOnScroll) -->
    <div class="features-section">
        <div class="features-grid">
            <UiAnimateOnScroll
                v-for="(feature, index) in features"
                :key="feature.title"
                animation="fade-up"
                :delay="index * 100"
            >
                <div class="feature-card">
                    <div class="feature-icon">
                        <UIcon :name="feature.icon" class="text-2xl" />
                    </div>
                    <h3 class="feature-title">{{ feature.title }}</h3>
                    <p class="feature-description">{{ feature.description }}</p>
                </div>
            </UiAnimateOnScroll>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.hero-container {
    @apply flex-1 flex items-center justify-center px-4 py-12;
    @apply relative overflow-hidden;
}

/* Decorative gradient blobs */
.blob {
    @apply absolute rounded-full opacity-30 blur-3xl;
    @apply pointer-events-none;
}

.blob-1 {
    @apply w-96 h-96 -top-20 -right-20;
    background: linear-gradient(135deg, theme('colors.accent.400'), theme('colors.primary.500'));
    animation: drift-1 20s ease-in-out infinite;
}

.blob-2 {
    @apply w-80 h-80 -bottom-10 -left-10;
    background: linear-gradient(135deg, theme('colors.primary.500'), theme('colors.pop.400'));
    animation: drift-2 25s ease-in-out infinite;
}

@keyframes drift-1 {
    0%,
    100% {
        transform: translate(0, 0) rotate(0deg) scale(1);
    }
    25% {
        transform: translate(-50px, 35px) rotate(8deg) scale(1.03);
    }
    50% {
        transform: translate(-35px, -50px) rotate(-7deg) scale(0.97);
    }
    75% {
        transform: translate(40px, -25px) rotate(6deg) scale(1.02);
    }
}

@keyframes drift-2 {
    0%,
    100% {
        transform: translate(0, 0) rotate(0deg) scale(1);
    }
    25% {
        transform: translate(45px, -40px) rotate(-7deg) scale(1.04);
    }
    50% {
        transform: translate(30px, 45px) rotate(9deg) scale(0.96);
    }
    75% {
        transform: translate(-40px, 30px) rotate(-6deg) scale(1.03);
    }
}

.hero-content {
    @apply text-center max-w-2xl relative z-10;
}

.hero-title {
    @apply text-5xl md:text-6xl font-bold mb-6;
}

.hero-subtitle {
    @apply text-lg md:text-xl text-gray-600 dark:text-gray-400 mb-10;
    @apply max-w-xl mx-auto;
}

/* Tech badges with brand colors */
.tech-badges {
    @apply flex flex-wrap justify-center gap-3 mb-10;
}

.tech-badge {
    @apply inline-flex items-center gap-2 px-4 py-2 rounded-full;
    @apply text-sm font-medium;
    @apply transition-all duration-200;
}

.tech-badge:hover {
    @apply scale-105;
}

.tech-badge.accent {
    @apply bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-300;
}

.tech-badge.primary {
    @apply bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300;
}

.tech-badge.pop {
    @apply bg-pop-100 text-pop-700 dark:bg-pop-900/30 dark:text-pop-300;
}

.cta-section {
    @apply mb-10;
}

/* API Status */
.api-status {
    @apply flex items-center justify-center gap-2 text-sm;
}

.status-dot {
    @apply w-2 h-2 rounded-full;
}

.status-dot.online {
    @apply bg-green-500;
}

.status-dot.offline {
    @apply bg-red-500;
}

.status-dot.loading {
    @apply bg-yellow-500 animate-pulse;
}

.status-text {
    @apply text-gray-500 dark:text-gray-400;
}

/* Features Section */
.features-section {
    @apply py-16 px-4;
    @apply bg-white/50 dark:bg-slate-800/50;
    @apply border-t border-gray-200 dark:border-slate-700;
}

.features-grid {
    @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6;
    @apply max-w-6xl mx-auto;
}

.feature-card {
    @apply p-6 rounded-xl text-center;
    @apply bg-white dark:bg-slate-800;
    @apply border border-gray-200 dark:border-slate-700;
    @apply transition-all duration-300;
}

.feature-card:hover {
    @apply -translate-y-1 shadow-lg;
    @apply border-primary-300 dark:border-primary-600;
}

.feature-icon {
    @apply w-12 h-12 mx-auto mb-4 rounded-full;
    @apply flex items-center justify-center;
    @apply bg-primary-100 text-primary-600;
    @apply dark:bg-primary-900/30 dark:text-primary-400;
}

.feature-title {
    @apply font-semibold text-gray-900 dark:text-gray-100 mb-2;
}

.feature-description {
    @apply text-sm text-gray-600 dark:text-gray-400;
}
</style>
