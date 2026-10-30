<script setup>
const appBase = import.meta.env.BASE_URL
</script>

<template>
  <RouterLink class="brand" :to="{ name: 'home' }" aria-label="Buy in Minutes home">
    <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
  </RouterLink>
</template>
