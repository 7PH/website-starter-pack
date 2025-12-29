<script setup lang="ts">
const api = useApi();

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
    { name: 'Nuxt 3', icon: 'pi pi-desktop' },
    { name: 'FastAPI', icon: 'pi pi-bolt' },
    { name: 'PostgreSQL', icon: 'pi pi-database' },
    { name: 'Tailwind', icon: 'pi pi-palette' },
];
</script>

<template>
    <div class="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center px-4">
        <div class="text-center max-w-2xl">
            <h1 class="text-4xl md:text-5xl font-bold mb-4">Website Starter Pack</h1>
            <p class="text-lg text-gray-600 dark:text-gray-400 mb-8">
                Full-stack web application template with Nuxt 3, FastAPI, PostgreSQL, and Traefik.
            </p>

            <!-- Tech Stack -->
            <div class="flex flex-wrap justify-center gap-3 mb-8">
                <Tag v-for="tech in techStack" :key="tech.name" :value="tech.name" severity="secondary">
                    <template #icon>
                        <i :class="tech.icon" class="mr-1"></i>
                    </template>
                </Tag>
            </div>

            <!-- API Status -->
            <div class="flex items-center justify-center gap-2 text-sm">
                <span
                    class="w-2 h-2 rounded-full"
                    :class="{
                        'bg-green-500': apiStatus === 'online',
                        'bg-red-500': apiStatus === 'offline',
                        'bg-yellow-500 animate-pulse': apiStatus === 'loading',
                    }"
                ></span>
                <span class="text-gray-500">
                    API {{ apiStatus === 'online' ? 'Connected' : apiStatus === 'offline' ? 'Offline' : 'Checking...' }}
                </span>
            </div>
        </div>
    </div>
</template>
