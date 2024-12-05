<script lang="ts" setup>
import ModalLogin from '~/components/modal/ModalLogin.vue';

const modal = useModal();

function onSelectLogin() {
    console.log("Login clicked");
    modal.open(ModalLogin, { title: "Login" });
}
</script>

<template>
    <header class="flex justify-between px-6">
        <UNavigationMenu highlight :items="[
            {
                label: 'Home',
                to: '/'
            },
        ]" />
        <div>
            <UNavigationMenu highlight :items="[
                {
                    label: 'Login',
                    variant: 'link',
                    onSelect: () => onSelectLogin(),
                    class: 'cursor-pointer',
                },
            ]" />
        </div>
    </header>
</template>