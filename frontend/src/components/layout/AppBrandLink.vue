<script setup>
const appBase = import.meta.env.BASE_URL
</script>

<template>
  <RouterLink class="brand" :to="{ name: 'home' }" aria-label="Buy in Minutes home">
    <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
    <span class="brand-text">
      <span class="brand-name">Buy In Minutes</span>
      <span class="brand-tagline">Fresh market delivery</span>
    </span>
  </RouterLink>
</template>
