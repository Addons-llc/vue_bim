<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import DefaultLayout from './layouts/DefaultLayout.vue'
import CartPage from './pages/CartPage.vue'
import HomePage from './pages/HomePage.vue'
import LoginPage from './pages/LoginPage.vue'

const currentPath = ref(window.location.pathname)
const currentRoute = ref(getCurrentRoute())
const productSearchText = ref('')

function getCurrentRoute() {
  return window.location.hash.replace(/^#\/?/, '') || 'home'
}

function syncCurrentPath() {
  currentPath.value = window.location.pathname
  currentRoute.value = getCurrentRoute()
}

function navigateTo(path) {
  window.history.pushState({}, '', path)
  syncCurrentPath()
}

function navigateToLogin() {
  navigateTo('/login')
}

function navigateToCart() {
  window.location.hash = '/cart'
  currentRoute.value = 'cart'
}

function navigateToHome() {
  window.location.hash = ''
  currentRoute.value = 'home'
}

function updateProductSearch(searchText) {
  productSearchText.value = searchText
  navigateToHome()
}

onMounted(() => {
  window.addEventListener('popstate', syncCurrentPath)
  window.addEventListener('hashchange', syncCurrentPath)
})

onBeforeUnmount(() => {
  window.removeEventListener('popstate', syncCurrentPath)
  window.removeEventListener('hashchange', syncCurrentPath)
})
</script>

<template>
  <LoginPage v-if="currentPath === '/login'" />

  <DefaultLayout
    v-else
    @cart="navigateToCart"
    @logout="navigateToLogin"
    @search="updateProductSearch"
  >
    <HomePage :search-text="productSearchText" />
    <CartPage
      v-if="currentRoute === 'cart'"
      @continue-shopping="navigateToHome"
    />
  </DefaultLayout>
</template>
