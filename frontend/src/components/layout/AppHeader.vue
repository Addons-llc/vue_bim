<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppBrandLink from './AppBrandLink.vue'
import HeaderActions from './HeaderActions.vue'
import HeaderLocationPicker from './HeaderLocationPicker.vue'
import HeaderSearchForm from './HeaderSearchForm.vue'

const emit = defineEmits(['login', 'logout', 'search', 'wishlist'])
const route = useRoute()
const isCategoriesRoute = computed(() =>
  ['brands', 'stores', 'categories', 'category-details', 'store-details'].includes(route.name),
)
const isScrolled = ref(false)

function updateScrolled() {
  isScrolled.value = window.scrollY > 8
}

onMounted(() => {
  updateScrolled()
  window.addEventListener('scroll', updateScrolled, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateScrolled)
})
</script>

<template>
  <header
    class="app-header"
    :class="{ 'is-categories-page': isCategoriesRoute, 'is-scrolled': isScrolled }"
  >
    <div class="header-inner">
      <AppBrandLink />
      <HeaderLocationPicker />
      <HeaderSearchForm @search="emit('search', $event)" />
      <HeaderActions
        @login="emit('login')"
        @logout="emit('logout')"
        @wishlist="emit('wishlist')"
      />
    </div>
  </header>
</template>
