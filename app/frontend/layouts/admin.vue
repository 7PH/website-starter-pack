<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import AdminNav from '~/components/admin/AdminNav.vue';
import ImpersonationBanner from '~/components/admin/ImpersonationBanner.vue';
import ModalConfirm from '~/components/modal/ModalConfirm.vue';
</script>

<template>
    <UApp>
        <div class="admin-layout">
            <!-- Impersonation banner (if active) -->
            <ImpersonationBanner />

            <div class="admin-container">
                <!-- Sidebar -->
                <aside class="admin-sidebar">
                    <div class="sidebar-header">
                        <NuxtLink to="/" class="logo-link">
                            <UIcon name="i-lucide-arrow-left" />
                            <span>Back to Site</span>
                        </NuxtLink>
                    </div>
                    <AdminNav />
                </aside>

                <!-- Main content -->
                <main class="admin-main">
                    <NuxtPage />
                </main>
            </div>

            <!-- Global modals -->
            <ModalConfirm />
        </div>
    </UApp>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.admin-layout {
    @apply min-h-screen bg-gray-50 dark:bg-gray-900;
}

.admin-container {
    @apply flex min-h-screen;
}

.admin-sidebar {
    @apply w-64 bg-white dark:bg-gray-800 flex flex-col fixed top-0 left-0 bottom-0 z-40;
    @apply border-r-2 border-primary-500;
}

.sidebar-header {
    @apply p-4 border-b border-gray-100 dark:border-gray-700;
}

.logo-link {
    @apply flex items-center gap-2 text-gray-600 dark:text-gray-300 no-underline text-sm font-medium transition-colors;
}

.logo-link:hover {
    @apply text-primary-500;
}

.admin-main {
    @apply flex-1 ml-64 p-6;
}
</style>
