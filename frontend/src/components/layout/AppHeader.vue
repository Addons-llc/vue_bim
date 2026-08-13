<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppBrandLink from './AppBrandLink.vue'
import HeaderActions from './HeaderActions.vue'
import HeaderLocationPicker from './HeaderLocationPicker.vue'
import HeaderSearchForm from './HeaderSearchForm.vue'

const emit = defineEmits(['cart', 'login', 'logout', 'search', 'wishlist'])
const route = useRoute()
const isCategoriesRoute = computed(() =>
  ['brands', 'stores', 'categories', 'category-details', 'store-details'].includes(route.name),
)
</script>

<template>
  <header class="app-header" :class="{ 'is-categories-page': isCategoriesRoute }">
    <div class="header-inner">
      <AppBrandLink />
      <HeaderLocationPicker />
      <HeaderSearchForm @search="emit('search', $event)" />
      <HeaderActions
        @cart="emit('cart')"
        @login="emit('login')"
        @logout="emit('logout')"
        @wishlist="emit('wishlist')"
      />
    </div>
  </header>
</template>
