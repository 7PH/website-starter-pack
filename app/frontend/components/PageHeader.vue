<script lang="ts" setup>
const auth = useAuth();
const authActions = useAuthActions();
const { t } = useI18n();
const { isPremium, loading: subscriptionLoading } = useSubscription();
const { locale, availableLocales, setLocale } = useLocale();
const { isDark, toggle: toggleColorMode } = useColorModeToggle();

const localeMenu = ref();
const localeMenuItems = computed(() =>
    availableLocales.value.map((l) => ({
        label: l.name,
        command: () => setLocale(l.code),
    })),
);

const menuItems = ref([
    {
        label: 'Home',
        route: '/',
    },
]);

function onSelectLogout() {
    authActions.logout();
}

function toggleLocaleMenu(event: Event) {
    localeMenu.value.toggle(event);
}
</script>

<template>
    <Menubar :model="menuItems">
        <template #item="{ item }">
            <NuxtLink :to="item.route" class="p-menubar-item-link">
                <span>{{ item.label }}</span>
            </NuxtLink>
        </template>
        <template #end>
            <div class="flex items-center gap-3">
                <ClientOnly>
                    <!-- Logged out state -->
                    <template v-if="!auth.isLoggedIn">
                        <div class="flex items-center gap-2">
                            <NuxtLink to="/login">
                                <Button :label="t('core.auth.login')" text />
                            </NuxtLink>
                            <NuxtLink to="/login?mode=signup">
                                <Button :label="t('core.auth.register')" />
                            </NuxtLink>
                        </div>
                    </template>

                    <!-- Logged in state -->
                    <template v-else>
                        <div class="flex items-center gap-3">
                            <!-- Premium badge or Upgrade CTA -->
                            <NuxtLink
                                v-if="!subscriptionLoading"
                                to="/premium"
                                :class="isPremium ? 'premium-badge' : 'upgrade-cta'"
                            >
                                <i class="pi pi-star" :class="isPremium ? 'text-amber-400' : 'text-violet-500'" />
                                <span>{{ isPremium ? t('core.billing.premium') : t('core.billing.upgrade') }}</span>
                            </NuxtLink>
                            <span class="text-sm">
                                {{ auth.user?.first_name }}
                            </span>
                            <Button :label="t('core.auth.logout')" text severity="secondary" @click="onSelectLogout" />
                        </div>
                    </template>

                    <!-- Placeholder during SSR - reserves space -->
                    <template #fallback>
                        <div class="flex items-center gap-2 invisible">
                            <Button label="Login" text />
                            <Button label="Register" />
                        </div>
                    </template>

                    <!-- Theme Toggle -->
                    <Button
                        :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
                        severity="secondary"
                        text
                        rounded
                        aria-label="Toggle dark mode"
                        @click="toggleColorMode"
                    />

                    <!-- Language Switcher -->
                    <Button
                        :label="locale.toUpperCase()"
                        text
                        severity="secondary"
                        size="small"
                        @click="toggleLocaleMenu"
                    />
                    <Menu ref="localeMenu" :model="localeMenuItems" :popup="true" />
                </ClientOnly>
            </div>
        </template>
    </Menubar>
</template>

<style scoped>
.premium-badge,
.upgrade-cta {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
}

.premium-badge {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    color: #92400e;
}

.premium-badge:hover {
    background: linear-gradient(135deg, #fde68a 0%, #fcd34d 100%);
}

.upgrade-cta {
    background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
    color: #5b21b6;
}

.upgrade-cta:hover {
    background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%);
}
</style>
