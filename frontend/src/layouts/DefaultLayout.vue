<script setup>
import { useRoute } from 'vue-router'
import AppFooter from '../components/layout/AppFooter.vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppMobileNav from '../components/layout/AppMobileNav.vue'
import FloatingCart from '../components/layout/FloatingCart.vue'
import CartNotice from '../components/layout/CartNotice.vue'

const emit = defineEmits(['login', 'logout', 'wishlist'])
const route = useRoute()
</script>

<template>
  <AppHeader
    v-if="!route.meta.hideHeader"
    @login="emit('login')"
    @logout="emit('logout')"
    @wishlist="emit('wishlist')"
  />

  <main class="page-shell">
    <slot />
  </main>

  <AppFooter />

  <FloatingCart />

  <CartNotice />

  <AppMobileNav />
</template>
