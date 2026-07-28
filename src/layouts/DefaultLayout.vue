<script setup>
import AppFooter from '../components/layout/AppFooter.vue'
import AppHeader from '../components/layout/AppHeader.vue'

const emit = defineEmits(['cart', 'logout', 'search'])
</script>

<template>
  <AppHeader
    @cart="emit('cart')"
    @logout="emit('logout')"
    @search="emit('search', $event)"
  />

  <main class="page-shell">
    <slot />
  </main>

  <AppFooter />
</template>
