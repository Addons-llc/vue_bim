<script setup>
import AppFooter from '../components/layout/AppFooter.vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppMobileNav from '../components/layout/AppMobileNav.vue'
import FloatingCart from '../components/layout/FloatingCart.vue'

const emit = defineEmits(['login', 'logout', 'search', 'wishlist'])
</script>

<template>
  <AppHeader
    @login="emit('login')"
    @logout="emit('logout')"
    @search="emit('search', $event)"
    @wishlist="emit('wishlist')"
  />

  <main class="page-shell">
    <slot />
  </main>

  <AppFooter />

  <FloatingCart />

  <AppMobileNav />
</template>
