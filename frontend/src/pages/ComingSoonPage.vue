<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <section class="coming-soon-page">
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    <RouterLink class="coming-soon-page-link" :to="{ name: 'home' }">Continue shopping</RouterLink>
  </section>
</template>
