<script setup lang="ts">
useAuth()
  .init()
  .then(() => {
    console.log('Auth initialized');
  });
</script>

<template>
  <div>
    <NuxtLayout />
  </div>
</template>
