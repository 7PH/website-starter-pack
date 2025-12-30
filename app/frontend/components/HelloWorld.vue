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
</script>

<template>
    <div class="hero-container">
        <!-- Decorative blobs -->
        <div class="blob blob-1" />
        <div class="blob blob-2" />

        <div class="hero-content">
            <h1 class="hero-title text-gradient-brand">Website Starter Pack</h1>
            <p class="hero-subtitle">
                Full-stack web application template with Nuxt 3, FastAPI, PostgreSQL, and Traefik.
            </p>

            <!-- Tech Stack Badges -->
            <div class="tech-badges">
                <span v-for="tech in techStack" :key="tech.name" :class="['tech-badge', tech.color]">
                    <UIcon :name="tech.icon" />
                    {{ tech.name }}
                </span>
            </div>

            <!-- CTA Button -->
            <div class="cta-section">
                <UiGradientButton size="lg" @click="modal.open('auth', { initialMode: 'signup' })">
                    <UIcon name="i-lucide-arrow-right" class="mr-2" />
                    Get Started
                </UiGradientButton>
            </div>

            <!-- API Status -->
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
                    API {{ apiStatus === 'online' ? 'Connected' : apiStatus === 'offline' ? 'Offline' : 'Checking...' }}
                </span>
            </div>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.hero-container {
    @apply min-h-[calc(100vh-4rem)] flex items-center justify-center px-4;
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
}

.blob-2 {
    @apply w-80 h-80 -bottom-10 -left-10;
    background: linear-gradient(135deg, theme('colors.primary.500'), theme('colors.pop.400'));
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
</style>
