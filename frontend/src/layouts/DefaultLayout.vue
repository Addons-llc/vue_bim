<script setup>
import AppFooter from '../components/layout/AppFooter.vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppMobileNav from '../components/layout/AppMobileNav.vue'

const emit = defineEmits(['cart', 'login', 'logout', 'search', 'wishlist'])
</script>

<template>
  <AppHeader
    @cart="emit('cart')"
    @login="emit('login')"
    @logout="emit('logout')"
    @search="emit('search', $event)"
    @wishlist="emit('wishlist')"
  />

  <main class="page-shell">
    <slot />
  </main>

  <AppFooter />

  <AppMobileNav @login="emit('login')" />
</template>
